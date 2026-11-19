# Extent of the clipping fix

Forest summaries draw the pooled and subgroup fitted CIs through the shared diamond renderer. Its clipped edge now ends in a tip on the specified bound. An entirely excluded diamond is represented by an outward tip at the nearest edge.

The existing forest prediction interval is only a text footer. The three ordinary styles and sequential/subgroup fallbacks call rcmetar.forest.prediction.label. There is no plotted prediction interval to clip. The displayed prediction limits remain in the footer and no new prediction glyph was introduced.
