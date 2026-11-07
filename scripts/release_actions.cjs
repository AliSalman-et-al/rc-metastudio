// GitHub operations shared by the two candidate consumers; no shell parsing.
async function validateCandidate({ github, context, runId, sourceSha }) {
  if (!/^[1-9][0-9]*$/.test(runId) || !/^[0-9a-f]{40}$/.test(sourceSha))
    throw Error("Invalid run ID or source SHA");
  const repo = context.repo;
  const fullName = `${repo.owner}/${repo.repo}`;
  const { data: run } = await github.rest.actions.getWorkflowRun({
    ...repo,
    run_id: Number(runId),
  });
  if (
    run.conclusion !== "success" ||
    run.event !== "workflow_dispatch" ||
    run.path !== ".github/workflows/candidate.yml" ||
    run.head_branch !== "master" ||
    !/^[0-9a-f]{40}$/.test(run.head_sha) ||
    run.repository?.full_name !== fullName ||
    run.head_repository?.full_name !== fullName
  )
    throw Error("Unauthorized candidate producer");
  // Dispatch workflow revision and selected build source may be different old
  // master commits. Both must belong to protected master, never a fork/PR head.
  for (const sha of [run.head_sha, sourceSha]) {
    const { data } = await github.rest.repos.compareCommitsWithBasehead({
      ...repo,
      basehead: `master...${sha}`,
    });
    if (!["identical", "behind"].includes(data.status))
      throw Error("Candidate revision is not on master");
  }
}

async function withdraw({ github, context, tag, replacement, reason }) {
  if (
    !/^v[0-9]+\.[0-9]+\.[0-9]+$/.test(tag) ||
    !/^v[0-9]+\.[0-9]+\.[0-9]+$/.test(replacement) ||
    tag === replacement ||
    !reason?.trim()
  )
    throw Error("Invalid withdrawal or replacement");
  const repo = context.repo;
  const { data: release } = await github.rest.repos.getReleaseByTag({
    ...repo,
    tag,
  });
  const { data: good } = await github.rest.repos.getReleaseByTag({
    ...repo,
    tag: replacement,
  });
  if (good.draft || good.prerelease || good.body?.includes("WITHDRAWN:"))
    throw Error("Replacement must be an available stable release");
  const title = `Release ${tag} withdrawn`;
  const marker = `<!-- rcms-withdrawal:${tag} -->`;
  const notice = `WITHDRAWN: ${reason} Replacement/last-known-good: ${replacement}. Assets and evidence are retained for audit.`;
  const issues = await github.paginate(github.rest.issues.listForRepo, {
    ...repo,
    state: "all",
    per_page: 100,
  });
  const matching = issues.filter(
    (issue) =>
      !issue.pull_request &&
      issue.title === title &&
      issue.body?.includes(marker),
  );
  if (matching.length > 1) throw Error("Ambiguous withdrawal tracking issues");
  let issue = matching[0];
  if (issue && !issue.body.includes(notice))
    throw Error("Withdrawal retry differs from tracked request");
  // Create the audit record first. An edit failure leaves a tracked pending
  // withdrawal; rerun the same request to resume. Never roll back safety state.
  if (!issue)
    ({ data: issue } = await github.rest.issues.create({
      ...repo,
      title,
      body: `${marker}\n${notice}`,
      labels: ["bug"],
    }));
  if (!release.body?.includes(marker)) {
    await github.rest.repos.updateRelease({
      ...repo,
      release_id: release.id,
      prerelease: true,
      body: `${marker}\n${notice}\nTracking: ${issue.html_url}\n\n${release.body || ""}`,
    });
  }
}

module.exports = { validateCandidate, withdraw };

if (require.main === module) {
  const { execFileSync } = require("node:child_process");
  const repository = process.env.GITHUB_REPOSITORY;
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository || ""))
    throw Error("Invalid repository");
  const [owner, repo] = repository.split("/");
  const api = (path, method = "GET", body) =>
    JSON.parse(
      execFileSync(
        "gh",
        ["api", path, "--method", method, ...(body ? ["--input", "-"] : [])],
        { encoding: "utf8", input: body ? JSON.stringify(body) : undefined },
      ),
    );
  const prefix = `repos/${repository}`;
  const github = {
    rest: {
      actions: {
        getWorkflowRun: async ({ run_id }) => ({
          data: api(`${prefix}/actions/runs/${run_id}`),
        }),
      },
      repos: {
        compareCommitsWithBasehead: async ({ basehead }) => ({
          data: api(`${prefix}/compare/${basehead}`),
        }),
        getReleaseByTag: async ({ tag }) => ({
          data: api(`${prefix}/releases/tags/${encodeURIComponent(tag)}`),
        }),
        updateRelease: async ({ release_id, body, prerelease }) => ({
          data: api(`${prefix}/releases/${release_id}`, "PATCH", {
            body,
            prerelease,
          }),
        }),
      },
      issues: {
        listForRepo: () => {},
        create: async ({ title, body, labels }) => ({
          data: api(`${prefix}/issues`, "POST", { title, body, labels }),
        }),
      },
    },
    paginate: async () =>
      JSON.parse(
        execFileSync(
          "gh",
          [
            "api",
            `${prefix}/issues?state=all&per_page=100`,
            "--paginate",
            "--slurp",
          ],
          { encoding: "utf8" },
        ),
      ).flat(),
  };
  const context = { repo: { owner, repo } };
  const command = process.argv[2];
  const operation =
    command === "validate-candidate"
      ? validateCandidate({
          github,
          context,
          runId: process.env.RUN_ID,
          sourceSha: process.env.EXPECTED_SOURCE_SHA,
        })
      : command === "withdraw"
        ? withdraw({
            github,
            context,
            tag: process.env.TAG,
            replacement: process.env.SUPERSEDED_BY,
            reason: process.env.REASON,
          })
        : Promise.reject(Error("Unknown release operation"));
  operation.catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}
