# DevAgent Benchmark Evaluation Report

## Summary Metrics

- **Verified Resolution Rate**: `100.0%` (5/5 cases)
- **Average Iterations**: `6.0` / 8 max turns
- **Average Tool Calls**: `5.0` calls
- **Average Verification Runs**: `1.0` runs
- **Average Patch Size**: `3.2` lines changed
- **Average Runtime**: `0.13s`

## Detailed Benchmark Breakdown

| Case ID | Name | Status | Iterations | Tool Calls | Patch Lines | Runtime |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `case_001_guest_session` | Guest Checkout Session Expiry 401 | ✅ PASSED | 6 | 5 | 2 | 0.13s |
| `case_002_cart_tax` | Cart Total Tax Calculation Omission | ✅ PASSED | 6 | 5 | 5 | 0.13s |
| `case_003_catalog_pagination` | Catalog Pagination Off-By-One Truncation | ✅ PASSED | 6 | 5 | 3 | 0.12s |
| `case_004_user_null_name` | User Null Display Name AttributeError | ✅ PASSED | 6 | 5 | 4 | 0.13s |
| `case_005_cart_creation_status` | Cart Creation Endpoint 404 Status Bug | ✅ PASSED | 6 | 5 | 2 | 0.13s |
