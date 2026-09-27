export interface AuditLog {
  timestamp: string;
  stage: string;
  agent: string;
  action: string;
  status: 'IN_PROGRESS' | 'SUCCESS' | 'WARNING' | 'FAILED' | 'PAUSED';
  details: string;
}

export interface GitCommit {
  hash: string;
  short_hash: string;
  author: string;
  email: string;
  timestamp: string;
  message: string;
  stage: string;
  files_changed: string[];
}

export interface RequirementsDoc {
  title: string;
  overview?: string;
  problem_statement?: string;
  reasoning?: string;
  functional_requirements: Array<{
    id: string;
    title?: string;
    description: string;
    acceptance_criteria?: string[];
  }>;
  non_functional_requirements: Array<{
    category: string;
    requirement?: string;
    description?: string;
  }>;
  constraints: string[];
  assumptions: string[];
  acceptance_criteria?: string[];
}

export interface ArchitectureDoc {
  system_overview: string;
  reasoning?: string;
  design_patterns: string[];
  data_flow: string;
  modules?: Array<{
    name: string;
    file_path?: string;
    purpose?: string;
    exports?: string[];
    dependencies?: string[];
  }>;
  module_specifications?: Array<{
    name: string;
    responsibility?: string;
    purpose?: string;
    public_interfaces?: string[];
    exports?: string[];
    dependencies?: string[];
  }>;
  folder_structure?: string;
  file_structure?: Array<{
    path: string;
    description: string;
  }>;
  interfaces?: string[];
}

export interface CodeReviewIssue {
  severity: 'CRITICAL' | 'MAJOR' | 'MINOR' | 'INFO';
  file: string;
  line_number?: number;
  description: string;
  recommendation: string;
}

export interface CodeReviewDoc {
  overall_score: number;
  passed: boolean;
  summary: string;
  reasoning?: string;
  architecture_adherence: boolean;
  issues: CodeReviewIssue[];
  strengths: string[];
}

export interface TestResult {
  tests_total: number;
  tests_passed: number;
  tests_failed: number;
  tests_errored: number;
  stdout: string;
  stderr: string;
  duration_seconds: number;
  success: boolean;
  error_message?: string;
  reasoning?: string;
}

export interface BugFixEntry {
  iteration: number;
  diagnosis: string;
  patches_applied: string[];
  test_pass_before: string;
  test_pass_after: string;
  success: boolean;
  reasoning?: string;
}

export interface DocumentationBundle {
  readme: string;
  setup_instructions: string;
  reasoning?: string;
  module_documentation: Record<string, string>;
  build_summary: {
    total_modules: number;
    pipeline_stages_completed: number;
    test_pass_rate: string;
    git_commits_created: number;
    status: string;
  };
}

export interface PendingApproval {
  stage: 'Requirements' | 'Architecture' | 'Code Review' | string;
  title: string;
  artifact_type: 'requirements' | 'architecture' | 'review' | string;
  artifact: any;
}

export interface ApprovalHistoryItem {
  id: string;
  stage: string;
  action: 'APPROVED' | 'CHANGES_REQUESTED' | 'REJECTED';
  timestamp: string;
  reviewer: string;
  feedback?: string | null;
  artifact_summary?: string;
}

export interface GitHubPushResult {
  success: boolean;
  repo_url?: string;
  owner?: string;
  repo_name?: string;
  commits_pushed?: number;
  message?: string;
  error?: string;
}

export interface PipelineState {
  requirement: string;
  project_dir: string;
  audit_logs: AuditLog[];
  git_commits: GitCommit[];
  code_files: Record<string, string>;
  codegen_reasoning?: string;
  test_files: Record<string, string>;
  requirements_doc: RequirementsDoc | null;
  architecture_doc: ArchitectureDoc | null;
  review_doc: CodeReviewDoc | null;
  security_report?: any;
  static_analysis?: any;
  coverage_report?: any;
  test_result: TestResult | null;
  bugfix_history: BugFixEntry[];
  bugfix_iteration: number;
  documentation: DocumentationBundle | null;
  cicd_package?: any;
  stage_traces?: any[];
  total_tokens?: number;
  total_cost_usd?: number;
  current_stage: string;
  max_iterations: number;
  provider_type: string;
  error_message?: string | null;
  require_approval?: boolean;
  feature_flags?: FeatureFlags;
  pipeline_status?: 'IDLE' | 'RUNNING' | 'PAUSED_FOR_APPROVAL' | 'PAUSED_FOR_CLARIFICATION' | 'COMPLETED' | 'STOPPED' | 'ESCALATED' | 'FAILED';
  pending_approval?: PendingApproval | null;
  approval_history?: ApprovalHistoryItem[];
  clarification_questions?: Array<{
    id: string;
    question: string;
    category: string;
    answered: boolean;
    answer?: string;
  }>;
  escalation_info?: any;
}

export interface PresetRequirement {
  id: string;
  title: string;
  badge: string;
  prompt: string;
  description: string;
}

export interface FeatureFlags {
  clarification_loop: boolean;    // Always ON
  hitl_checkpoints: boolean;       // OFF by default
  security_review: boolean;        // ON by default
  static_analysis: boolean;        // ON by default
  bugfix_escalation: boolean;      // ON by default
  regression_testing: boolean;     // ON by default
  coverage_reporting: boolean;     // ON by default
  cicd_scaffolding: boolean;       // OFF by default
  trace_dashboard: boolean;        // ON by default
  live_stream: boolean;            // OFF by default
}
