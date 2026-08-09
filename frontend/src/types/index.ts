// ─────────────────────────────────────────────────────────────────────────────
//  CloudPilot TypeScript types
// ─────────────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export type ProjectStatus =
  | 'CREATED'
  | 'ANALYZING'
  | 'DEPLOYING'
  | 'RUNNING'
  | 'FAILED'
  | 'STOPPED';

export interface Project {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
  };
}

// ── Form payloads ─────────────────────────────────────────────────────────────

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface CreateProjectPayload {
  name: string;
  description?: string;
}

export interface UpdateProjectPayload {
  name?: string;
  description?: string;
  status?: ProjectStatus;
}

// ── Auth context ──────────────────────────────────────────────────────────────

export interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
}

// ── Phase 2: Repository Analysis Types ────────────────────────────────────────

export type AnalysisStatus =
  | 'PENDING'
  | 'CLONING'
  | 'SCANNING'
  | 'ANALYZING'
  | 'COMPLETED'
  | 'FAILED';

export interface DetectionItem {
  name: string;
  confidence: number;
  evidence: string[];
}

export interface DatabaseDetection {
  name: string;
  confidence: number;
  certainty: 'Detected' | 'Likely' | 'Possible';
  evidence: string[];
}

export interface PortInfo {
  port: number;
  service: string;
  port_type: string;
  source: string;
}

export interface EnvVarInfo {
  name: string;
  sensitive: boolean;
  source: string;
}

export interface ServiceInfo {
  name: string;
  type: 'application' | 'database' | 'cache' | 'queue' | 'worker';
  runtime?: string | null;
  framework?: string | null;
  port?: number | null;
  confidence: number;
  evidence: string[];
}

export interface DockerInfo {
  detected: boolean;
  has_dockerfile: boolean;
  has_compose: boolean;
  base_image?: string | null;
  exposed_ports: number[];
  workdir?: string | null;
  compose_services: string[];
}

export interface LanguageDistribution {
  primary: string;
  distribution: Record<string, number>;
}

export interface RepositoryInfo {
  owner: string;
  name: string;
  url: string;
  commit_sha?: string | null;
}

export interface RepositoryProfile {
  repository: RepositoryInfo;
  languages: LanguageDistribution;
  package_managers: string[];
  frameworks: DetectionItem[];
  dependencies: Record<string, string[]>;
  databases: DatabaseDetection[];
  caches: DetectionItem[];
  queues: DetectionItem[];
  containers: DockerInfo;
  ports: PortInfo[];
  environment_variables: EnvVarInfo[];
  services: ServiceInfo[];
  is_monorepo: boolean;
  monorepo_apps: string[];
  readme_summary?: string | null;
}

export interface RepositoryAnalysis {
  id: string;
  project_id: string;
  repository_url: string;
  repository_owner: string | null;
  repository_name: string | null;
  commit_sha: string | null;
  status: AnalysisStatus;
  progress: number;
  primary_language: string | null;
  analysis_result: RepositoryProfile | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

// ── Phase 3: AI Infrastructure Plan Types ─────────────────────────────────────

export type PlanStatus =
  | 'PENDING'
  | 'GENERATING'
  | 'VALIDATING'
  | 'COMPLETED'
  | 'FAILED';

export interface ReplicasConfig {
  min: number;
  max: number;
  initial: number;
}

export interface ServiceDefinition {
  id: string;
  name: string;
  type: 'application' | 'worker' | 'database' | 'cache' | 'queue' | 'storage' | 'gateway';
  runtime?: string | null;
  framework?: string | null;
  source_path?: string | null;
  port?: number | null;
  protocol: 'http' | 'https' | 'tcp' | 'udp';
  public: boolean;
  replicas: ReplicasConfig;
  scalable: boolean;
  confidence: number;
  evidence: string[];
}

export interface ServiceDependency {
  source: string;
  target: string;
  dependency_type: 'database' | 'cache' | 'queue' | 'http' | 'other';
  required: boolean;
}

export interface NetworkDefinition {
  name: string;
  type: 'private' | 'public' | 'overlay';
}

export interface VolumeDefinition {
  name: string;
  service: string;
  persistent: boolean;
  mount_path: string;
}

export interface EnvironmentVariable {
  name: string;
  source?: string | null;
  secret: boolean;
  required: boolean;
  default?: string | null;
}

export interface ServiceEnvironment {
  service: string;
  variables: EnvironmentVariable[];
}

export interface ScalingPolicy {
  service: string;
  metric: 'cpu' | 'memory' | 'request_count' | 'p95_latency';
  scale_up_threshold: number;
  scale_down_threshold: number;
  cooldown_seconds: number;
}

export interface ResourceProfile {
  service: string;
  cpu: string;
  memory: string;
  confidence: number;
  reason: string;
}

export interface HealthCheck {
  service: string;
  type: 'http' | 'tcp' | 'command';
  path?: string | null;
  port?: number | null;
  interval_seconds: number;
  timeout_seconds: number;
  failure_threshold: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  runtime?: string | null;
  framework?: string | null;
  public: boolean;
  replicas: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  label: string;
  dependency_type: string;
}

export interface ArchitectureGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface RiskItem {
  risk: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  mitigation?: string | null;
}

export interface AIExplanation {
  summary: string;
  architecture_choice: string;
  scaling_reasoning: string;
  security_notes: string;
}

export interface ApplicationInfo {
  name: string;
  architecture_type: 'single_service' | 'multi_service' | 'monorepo';
}

export interface InfrastructurePlan {
  plan_version: string;
  generated_at?: string | null;
  analyzer_version: string;
  planner_version: string;
  application: ApplicationInfo;
  services: ServiceDefinition[];
  networks: NetworkDefinition[];
  volumes: VolumeDefinition[];
  dependencies: ServiceDependency[];
  environment: ServiceEnvironment[];
  scaling: ScalingPolicy[];
  health_checks: HealthCheck[];
  resource_profiles: ResourceProfile[];
  risks: RiskItem[];
  graph: ArchitectureGraph;
  explanation: AIExplanation;
  deployment_order: string[];
}

export interface PlanRead {
  id: string;
  project_id: string;
  repository_analysis_id: string;
  version: number;
  status: PlanStatus;
  ai_provider: string | null;
  ai_model: string | null;
  generation_duration_ms: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface PlanResultRead extends PlanRead {
  plan_data: InfrastructurePlan | null;
  validation_result: {
    passed: boolean;
    fallback_used?: boolean;
    attempts?: number;
    errors?: string[];
  } | null;
}

// ── Phase 5: Deployment & Health Check Engine Types
export type HealthStatus = 'UNKNOWN' | 'STARTING' | 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY' | 'FAILED';

export interface ServiceHealthRead {
  id: string;
  deployment_service_id: string;
  service_id: string;
  status: HealthStatus;
  consecutive_failures: number;
  consecutive_successes: number;
  latency_ms?: number;
  last_check_at?: string;
  last_success_at?: string;
  last_failure_at?: string;
  last_error?: string;
  updated_at: string;
}

export interface DeploymentHealthRead {
  deployment_id: string;
  status: HealthStatus;
  overall_health: HealthStatus;
  services: Record<string, HealthStatus>;
  avg_latency_ms?: number;
}

export interface HealthCheckRecord {
  id: string;
  deployment_service_id: string;
  check_type: string;
  status: HealthStatus;
  latency_ms?: number;
  status_code?: number;
  error_message?: string;
  checked_at: string;
}

export interface HealthEvent {
  id: string;
  project_id: string;
  deployment_id: string;
  service_id: string;
  event_type: string;
  previous_state?: string;
  new_state: string;
  message: string;
  created_at: string;
}

// ── Phase 6: Real-Time Observability Platform Types ─────────────────────────

export interface ContainerMetricsRead {
  id: string;
  project_id: string;
  deployment_id: string;
  service_id: string;
  container_id: string;
  timestamp: string;
  cpu_percent: number;
  memory_usage_bytes: number;
  memory_limit_bytes?: number;
  memory_percent: number;
  network_rx_bytes: number;
  network_tx_bytes: number;
  network_rx_rate: number;
  network_tx_rate: number;
  block_read_bytes?: number;
  block_write_bytes?: number;
  restart_count: number;
  container_state: string;
}

export interface ServiceMetricsRead {
  service_id: string;
  timestamp: string;
  cpu_percent: number;
  memory_usage_bytes: number;
  memory_limit_bytes?: number;
  memory_percent: number;
  network_rx_rate: number;
  network_tx_rate: number;
  restart_count: number;
  container_state: string;
}

export interface DeploymentMetricsRead {
  deployment_id: string;
  timestamp: string;
  total_cpu_percent: number;
  avg_cpu_percent: number;
  total_memory_usage_bytes: number;
  avg_memory_percent: number;
  total_network_rx_rate: number;
  total_network_tx_rate: number;
  total_restarts: number;
  services: Record<string, ServiceMetricsRead>;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
}

export interface LogEntriesRead {
  service_id: string;
  lines: LogEntry[];
}

// ── Phase 4: Container & Orchestration Types ─────────────────────────────────

export type DeploymentStatus =
  | 'PENDING'
  | 'PREPARING'
  | 'BUILDING'
  | 'CREATING_NETWORK'
  | 'CREATING_VOLUMES'
  | 'CREATING_SERVICES'
  | 'STARTING'
  | 'RUNNING'
  | 'FAILED'
  | 'STOPPED';

export type ServiceDesiredState = 'RUNNING' | 'STOPPED';

export type ServiceActualState =
  | 'RUNNING'
  | 'STARTING'
  | 'EXITED'
  | 'CREATED'
  | 'FAILED'
  | 'UNKNOWN';

export interface DeploymentServiceInfo {
  id: string;
  deployment_id: string;
  service_id: string;
  container_id: string | null;
  container_name: string;
  image: string;
  desired_state: ServiceDesiredState;
  actual_state: ServiceActualState;
  status: string;
  port: number | null;
  public: boolean;
  started_at: string | null;
  stopped_at: string | null;
  error_message: string | null;
}

export interface DeploymentLogEntry {
  timestamp: string;
  message: string;
}

export interface DeploymentRead {
  id: string;
  project_id: string;
  infrastructure_plan_id: string;
  version: number;
  status: DeploymentStatus;
  progress: number;
  logs: DeploymentLogEntry[] | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  services: DeploymentServiceInfo[];
}

export interface ServiceLogsRead {
  service_id: string;
  container_name: string;
  logs: string;
}

// Phase 7: Traffic Generator & Deterministic Autoscaling
export interface ScalingPolicyRead {
  id: string;
  project_id: string;
  deployment_id: string;
  service_id: string;
  enabled: boolean;
  min_replicas: number;
  max_replicas: number;
  target_cpu: number | null;
  target_memory: number | null;
  target_request_rate: number | null;
  target_latency: number | null;
  scale_up_threshold: number | null;
  scale_down_threshold: number | null;
  scale_up_cooldown: number;
  scale_down_cooldown: number;
  stabilization_window: number;
  max_scale_up_step: number;
  max_scale_down_step: number;
  dry_run: boolean;
  simulation_mode: boolean;
  cooldown_remaining_seconds: number;
}

export interface ScalingDecisionRead {
  id: string;
  service_id: string;
  current_replicas: number;
  recommended_replicas: number;
  action: string;
  status: string;
  reason: string;
  trigger_metric: string | null;
  metric_value: number | null;
  target_value: number | null;
  metrics_json: Record<string, number | null> | null;
  created_at: string;
}

export interface ScalingEventRead {
  id: string;
  service_id: string;
  event_type: string;
  message: string;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
}

export type TrafficScenario = 'constant' | 'ramp_up' | 'ramp_down' | 'spike';
export interface TrafficRunRead {
  id: string;
  project_id: string;
  deployment_id: string;
  service_id: string;
  scenario: TrafficScenario;
  configuration: Record<string, number | string | null>;
  status: string;
  current_rps: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

// Phase 8: Failure Injection & Autonomous Self-Healing
export type FailureScenario = 'CONTAINER_STOP' | 'CONTAINER_KILL' | 'SERVICE_FAILURE' | 'REPLICA_FAILURE' | 'HEALTH_CHECK_FAILURE';
export interface FailureInjectionRead { id: string; project_id: string; deployment_id: string; service_id: string; target_container_id: string | null; scenario: FailureScenario; status: string; simulation: boolean; started_at: string | null; completed_at: string | null; created_at: string; }
export interface IncidentRead { id: string; project_id: string; deployment_id: string; service_id: string; severity: string; status: string; trigger: string; root_cause_service_id: string | null; root_cause_type: string | null; diagnosis: { root_service?: string; impacted_services?: string[]; evidence?: string[] } | null; opened_at: string; resolved_at: string | null; created_at: string; }
export interface RecoveryAttemptRead { id: string; incident_id: string; action: string; target_service_id: string; target_container_id: string | null; attempt_number: number; status: string; reason: string; started_at: string | null; completed_at: string | null; error_message: string | null; }
export interface RecoveryEventRead { id: string; incident_id: string; event_type: string; message: string; metadata_json: Record<string, unknown> | null; created_at: string; }
export interface IncidentAIAnalysis { summary: string; root_cause: { service?: string | null; type?: string; confidence?: string }; evidence: string[]; impact: string[]; recommendations: Array<{ action: string; target: string; reason: string; confidence: string }>; risk: string; status: string; fallback: boolean; cached: boolean; trace_id: string; validation: { accepted?: string[]; rejected?: string[]; fallback?: boolean }; }
