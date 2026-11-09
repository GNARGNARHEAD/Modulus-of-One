# Automated Checks

All runtime, instrument and research-certificate tests live here. Run the
single discovery command in the [development guide](../docs/software/DEVELOPMENT.md).

Tests build bounded temporary inputs. The frozen-analysis tests check both
acceptance and rejection conditions; passing them does not recreate missing
historical corpora or waive a frozen experiment's runtime/source requirements.
