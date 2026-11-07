const { test } = require("node:test");
const assert = require("node:assert/strict");
const {
  validateCandidate,
  withdraw,
} = require("../../../scripts/release_actions.cjs");

function fixture() {
  const run = {
    conclusion: "success",
    event: "workflow_dispatch",
    path: ".github/workflows/candidate.yml",
    head_branch: "master",
    head_sha: "a".repeat(40),
    repository: { full_name: "owner/repo" },
    head_repository: { full_name: "owner/repo" },
  };
  const calls = [];
  const releases = {
    "v1.0.0": {
      id: 1,
      body: "Original notes",
      draft: false,
      prerelease: false,
    },
    "v2.0.0": { id: 2, body: "Good", draft: false, prerelease: false },
  };
  const issues = [];
  const github = {
    rest: {
      actions: { getWorkflowRun: async () => ({ data: run }) },
      repos: {
        compareCommitsWithBasehead: async () => ({
          data: { status: "behind" },
        }),
        getReleaseByTag: async ({ tag }) => ({ data: releases[tag] }),
        updateRelease: async (args) => {
          calls.push("edit");
          Object.assign(releases["v1.0.0"], args);
        },
      },
      issues: {
        listForRepo: () => {},
        create: async (args) => {
          calls.push("issue");
          issues.push(args);
          return {
            data: { number: 1, html_url: "https://example.invalid/issue/1" },
          };
        },
      },
    },
    paginate: async () => issues,
  };
  return {
    github,
    context: { repo: { owner: "owner", repo: "repo" } },
    run,
    calls,
    releases,
    issues,
  };
}

test("accept protected historical producer; reject foreign producer metadata", async () => {
  for (const field of [
    null,
    "event",
    "path",
    "head_branch",
    "head_sha",
    "repository",
    "head_repository",
  ]) {
    const f = fixture();
    if (field)
      f.run[field] = field.includes("repository")
        ? { full_name: "foreign/repo" }
        : "untrusted";
    const operation = validateCandidate({
      ...f,
      runId: "42",
      sourceSha: "b".repeat(40),
    });
    if (field) await assert.rejects(operation);
    else await operation;
  }
  const f = fixture();
  f.github.rest.repos.compareCommitsWithBasehead = async () => ({
    data: { status: "diverged" },
  });
  await assert.rejects(
    validateCandidate({ ...f, runId: "42", sourceSha: "b".repeat(40) }),
  );
});

test("withdraw rejects self and unusable replacements before effects", async () => {
  for (const invalid of ["self", "draft", "prerelease", "withdrawn"]) {
    const f = fixture();
    if (invalid === "withdrawn") f.releases["v2.0.0"].body = "WITHDRAWN: bad";
    else if (invalid !== "self") f.releases["v2.0.0"][invalid] = true;
    await assert.rejects(
      withdraw({
        ...f,
        tag: "v1.0.0",
        replacement: invalid === "self" ? "v1.0.0" : "v2.0.0",
        reason: "Bad",
      }),
    );
    assert.deepEqual(f.calls, []);
  }
});

test("issue failure leaves release alone; edit failure resumes without duplicate issue or notice", async () => {
  const f = fixture();
  const args = { ...f, tag: "v1.0.0", replacement: "v2.0.0", reason: "Bad" };
  const create = f.github.rest.issues.create;
  f.github.rest.issues.create = async () => {
    throw Error("issue unavailable");
  };
  await assert.rejects(withdraw(args));
  assert.deepEqual(f.calls, []);
  f.github.rest.issues.create = create;
  const update = f.github.rest.repos.updateRelease;
  f.github.rest.repos.updateRelease = async () => {
    throw Error("edit unavailable");
  };
  await assert.rejects(withdraw(args));
  assert.equal(f.issues.length, 1);
  f.github.rest.repos.updateRelease = update;
  await withdraw(args);
  await withdraw(args);
  assert.equal(f.issues.length, 1);
  assert.equal(f.releases["v1.0.0"].body.split("WITHDRAWN:").length, 2);
  assert.ok(f.releases["v1.0.0"].body.endsWith("Original notes"));
});
