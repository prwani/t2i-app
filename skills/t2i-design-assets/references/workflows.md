# Design asset workflows

## Best of N

1. Generate multiple image variations.
2. Evaluate each variation with selected layers.
3. Sort by composite score.
4. Save image files and a JSON ranking report.

## Multi-platform package

1. Map target formats to API-supported sizes.
2. Generate one image per format.
3. Save outputs with format-specific names.

## Production notes

Generated assets should be stored outside git. For Azure Container Apps, use session-local downloads for prototypes and Azure Blob Storage for persistent multi-user asset libraries.
