# Test matrix

Final committed run: `20261030T204942255262Z-234f24d6d2` at `234f24d6d2a7ab08852c633234abd10d551772c3`. Results below are from the definitive post-commit execution.

- Unit/regression suite: **43 passed, 0 failed, 0 skipped** (43 discovered).
- `compileall`: PASS, exit 0.
- `.claude/settings.json` JSON parse: PASS, exit 0.
- Controller `doctor`: PASS, exit 0; reports Python 3.14.9, Git 2.56.0, Chromium available, settings valid, and the hook non-sandbox warning. Claude CLI is absent.
- Test evidence origin: local process execution. Hook and browser-origin details are in their dedicated matrices.

| Discovered test | Result | Evidence |
|---|---:|---|
| `test_blind_receipt_invalidated_by_event_tampering (test_attestation_evidence.EvidenceTests.test_blind_receipt_invalidated_by_event_tampering)` | PASS | local unittest output |
| `test_blind_rejects_event_commit_or_digest_mismatch (test_attestation_evidence.EvidenceTests.test_blind_rejects_event_commit_or_digest_mismatch)` | PASS | local unittest output |
| `test_blind_rejects_external_or_duplicate_capture (test_attestation_evidence.EvidenceTests.test_blind_rejects_external_or_duplicate_capture)` | PASS | local unittest output |
| `test_blind_rejects_modified_screenshot_and_fake_events (test_attestation_evidence.EvidenceTests.test_blind_rejects_modified_screenshot_and_fake_events)` | PASS | local unittest output |
| `test_completion_requires_untampered_review_and_qa_receipts (test_attestation_evidence.EvidenceTests.test_completion_requires_untampered_review_and_qa_receipts)` | PASS | local unittest output |
| `test_review_pass_requires_report (test_attestation_evidence.EvidenceTests.test_review_pass_requires_report)` | PASS | local unittest output |
| `test_review_receipt_detects_tampering (test_attestation_evidence.EvidenceTests.test_review_receipt_detects_tampering)` | PASS | local unittest output |
| `test_review_rejects_stale_commit_and_contract (test_attestation_evidence.EvidenceTests.test_review_rejects_stale_commit_and_contract)` | PASS | local unittest output |
| `test_accessible_role_and_label_actions (test_blind_browser_controls.BlindBrowserControlsTests.test_accessible_role_and_label_actions)` | PASS | local unittest output |
| `test_controls_discovered_without_source_or_values (test_blind_browser_controls.BlindBrowserControlsTests.test_controls_discovered_without_source_or_values)` | PASS | local unittest output |
| `test_external_requests_are_blocked_and_recorded (test_blind_browser_controls.BlindBrowserControlsTests.test_external_requests_are_blocked_and_recorded)` | PASS | local unittest output |
| `test_sensitive_inputs_not_persisted (test_blind_browser_controls.BlindBrowserControlsTests.test_sensitive_inputs_not_persisted)` | PASS | local unittest output |
| `test_each_browser_error_category_fails (test_browser_diagnostics.BrowserDiagnosticsTests.test_each_browser_error_category_fails)` | PASS | local unittest output |
| `test_empty_diagnostics_are_accepted (test_browser_diagnostics.BrowserDiagnosticsTests.test_empty_diagnostics_are_accepted)` | PASS | local unittest output |
| `test_safe_summary_excludes_error_text_and_urls (test_browser_diagnostics.BrowserDiagnosticsTests.test_safe_summary_excludes_error_text_and_urls)` | PASS | local unittest output |
| `test_status_and_unapproved_execution_denied (test_controller.ControllerGitGates.test_status_and_unapproved_execution_denied)` | PASS | local unittest output |
| `test_duplicate_email_rejected (test_demo.FixtureTests.test_duplicate_email_rejected)` | PASS | local unittest output |
| `test_seeded_disposable_database (test_demo.FixtureTests.test_seeded_disposable_database)` | PASS | local unittest output |
| `test_signup_http_persistence_validation_duplicate_and_unknown_route (test_demo.LocalHttpContractTests.test_signup_http_persistence_validation_duplicate_and_unknown_route)` | PASS | local unittest output |
| `test_clean_positive_path_and_stale_evidence_block (test_full_lifecycle.FullLifecycleTests.test_clean_positive_path_and_stale_evidence_block)` | PASS | local unittest output |
| `test_native_host_is_not_claimed (test_observability_pilot.PilotTests.test_native_host_is_not_claimed)` | PASS | local unittest output |
| `test_real_git_and_hook_decision_pilot (test_observability_pilot.PilotTests.test_real_git_and_hook_decision_pilot)` | PASS | local unittest output |
| `test_contract_digest_changes_with_scenario (test_security.ContractIntegrityTests.test_contract_digest_changes_with_scenario)` | PASS | local unittest output |
| `test_duplicate_criteria_rejected (test_security.ContractIntegrityTests.test_duplicate_criteria_rejected)` | PASS | local unittest output |
| `test_invalid_slug_blocked (test_security.ContractIntegrityTests.test_invalid_slug_blocked)` | PASS | local unittest output |
| `test_no_noninteractive_approvals (test_security.ContractIntegrityTests.test_no_noninteractive_approvals)` | PASS | local unittest output |
| `test_bad_json_fails_closed (test_security.HookAdversarialTests.test_bad_json_fails_closed)` | PASS | local unittest output |
| `test_blind_browser_only_allow (test_security.HookAdversarialTests.test_blind_browser_only_allow)` | PASS | local unittest output |
| `test_blind_source_tool_deny (test_security.HookAdversarialTests.test_blind_source_tool_deny)` | PASS | local unittest output |
| `test_blind_terminal_bypass_patterns_deny (test_security.HookAdversarialTests.test_blind_terminal_bypass_patterns_deny)` | PASS | local unittest output |
| `test_nonblind_is_not_source_blocked (test_security.HookAdversarialTests.test_nonblind_is_not_source_blocked)` | PASS | local unittest output |
| `test_stop_human_pause_no_deadlock (test_security.HookAdversarialTests.test_stop_human_pause_no_deadlock)` | PASS | local unittest output |
| `test_unapproved_write_guard (test_security.HookAdversarialTests.test_unapproved_write_guard)` | PASS | local unittest output |
| `test_controller_records_status_transitions_without_reason (test_trace_events.TraceControllerTests.test_controller_records_status_transitions_without_reason)` | PASS | local unittest output |
| `test_agent_type_is_redacted_when_untrusted (test_trace_events.TraceCriterionTests.test_agent_type_is_redacted_when_untrusted)` | PASS | local unittest output |
| `test_controller_logs_individual_criterion_results (test_trace_events.TraceCriterionTests.test_controller_logs_individual_criterion_results)` | PASS | local unittest output |
| `test_denied_hook_and_failed_tool_are_traced_without_payload (test_trace_events.TraceHookTests.test_denied_hook_and_failed_tool_are_traced_without_payload)` | PASS | local unittest output |
| `test_config_registers_lifecycle_and_failure_events (test_trace_events.TraceSettingsTests.test_config_registers_lifecycle_and_failure_events)` | PASS | local unittest output |
| `test_native_claim_not_supported_by_synthetic_trace (test_trace_events.TraceUnitTests.test_native_claim_not_supported_by_synthetic_trace)` | PASS | local unittest output |
| `test_report_rejects_malformed_jsonl (test_trace_events.TraceUnitTests.test_report_rejects_malformed_jsonl)` | PASS | local unittest output |
| `test_trace_matrix_rejects_missing_observations (test_trace_events.TraceUnitTests.test_trace_matrix_rejects_missing_observations)` | PASS | local unittest output |
| `test_writer_never_serializes_secrets_or_payload (test_trace_events.TraceUnitTests.test_writer_never_serializes_secrets_or_payload)` | PASS | local unittest output |
| `test_invalid_signup_shows_accessible_error (test_ui_static.StaticChromiumChecks.test_invalid_signup_shows_accessible_error)` | PASS | local unittest output |
