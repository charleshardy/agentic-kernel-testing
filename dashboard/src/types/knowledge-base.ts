// Knowledge Base Type Definitions

export interface Article {
  id: string
  title: string
  slug: string
  summary: string
  content: string
  format: ContentFormat
  category: ArticleCategory
  type: ArticleType
  status: ArticleStatus
  visibility: ArticleVisibility
  author: ArticleAuthor
  contributors: ArticleContributor[]
  tags: string[]
  keywords: string[]
  metadata: ArticleMetadata
  versions: ArticleVersion[]
  currentVersion: string
  attachments: ArticleAttachment[]
  links: ArticleLink[]
  references: ArticleReference[]
  translations: ArticleTranslation[]
  analytics: ArticleAnalytics
  feedback: ArticleFeedback
  createdAt: string
  updatedAt: string
  publishedAt?: string
  archivedAt?: string
}

export interface ArticleAuthor {
  id: string
  name: string
  email: string
  avatar?: string
  bio?: string
  expertise: string[]
  role: string
}

export interface ArticleContributor {
  id: string
  name: string
  email: string
  role: ContributorRole
  contribution: string
  contributedAt: string
}

export interface ArticleMetadata {
  readingTime: number
  difficulty: DifficultyLevel
  audience: AudienceType[]
  prerequisites: string[]
  objectives: string[]
  lastReviewed?: string
  reviewedBy?: string
  accuracy: number
  completeness: number
  relevance: number
  customFields: Record<string, any>
}

export interface ArticleVersion {
  id: string
  version: string
  title: string
  content: string
  summary: string
  changes: VersionChange[]
  author: string
  createdAt: string
  status: VersionStatus
  approved: boolean
  approvedBy?: string
  approvedAt?: string
  notes?: string
}

export interface VersionChange {
  type: ChangeType
  section: string
  description: string
  before?: string
  after?: string
}

export interface ArticleAttachment {
  id: string
  name: string
  type: AttachmentType
  size: number
  url: string
  mimeType: string
  description?: string
  thumbnail?: string
  downloadCount: number
  uploadedAt: string
  uploadedBy: string
}

export interface ArticleLink {
  id: string
  type: LinkType
  title: string
  url: string
  description?: string
  external: boolean
  verified: boolean
  lastChecked?: string
  status: LinkStatus
}

export interface ArticleReference {
  id: string
  type: ReferenceType
  title: string
  author?: string
  source?: string
  url?: string
  date?: string
  isbn?: string
  doi?: string
  description?: string
}

export interface ArticleTranslation {
  locale: string
  title: string
  summary: string
  content: string
  status: TranslationStatus
  translator: string
  translatedAt: string
  reviewedBy?: string
  reviewedAt?: string
  accuracy: number
}

export interface ArticleAnalytics {
  views: number
  uniqueViews: number
  downloads: number
  shares: number
  bookmarks: number
  averageRating: number
  totalRatings: number
  searchRank: number
  popularityScore: number
  engagementScore: number
  bounceRate: number
  timeOnPage: number
  viewTrends: ViewTrend[]
  searchTerms: SearchTerm[]
  referrers: Referrer[]
}

export interface ViewTrend {
  date: string
  views: number
  uniqueViews: number
  duration: number
}

export interface SearchTerm {
  term: string
  count: number
  rank: number
}

export interface Referrer {
  source: string
  count: number
  percentage: number
}

export interface ArticleFeedback {
  averageRating: number
  totalRatings: number
  ratings: RatingDistribution
  comments: FeedbackComment[]
  suggestions: FeedbackSuggestion[]
  reports: FeedbackReport[]
}

export interface RatingDistribution {
  1: number
  2: number
  3: number
  4: number
  5: number
}

export interface FeedbackComment {
  id: string
  userId: string
  userName: string
  rating: number
  comment: string
  helpful: number
  notHelpful: number
  status: CommentStatus
  createdAt: string
  updatedAt?: string
  moderatedBy?: string
  moderatedAt?: string
}

export interface FeedbackSuggestion {
  id: string
  userId: string
  userName: string
  type: SuggestionType
  title: string
  description: string
  priority: SuggestionPriority
  status: SuggestionStatus
  votes: number
  implementedAt?: string
  implementedBy?: string
  createdAt: string
}

export interface FeedbackReport {
  id: string
  userId: string
  userName: string
  type: ReportType
  reason: string
  description: string
  status: ReportStatus
  reviewedBy?: string
  reviewedAt?: string
  action?: string
  createdAt: string
}

export interface SearchResult {
  id: string
  title: string
  summary: string
  url: string
  type: SearchResultType
  category: string
  relevanceScore: number
  matchType: MatchType
  highlights: SearchHighlight[]
  metadata: SearchMetadata
  lastUpdated: string
}

export interface SearchHighlight {
  field: string
  fragments: string[]
  matchedTerms: string[]
}

export interface SearchMetadata {
  author: string
  readingTime: number
  difficulty: DifficultyLevel
  views: number
  rating: number
  tags: string[]
  lastModified: string
}

export interface SearchQuery {
  query: string
  filters: SearchFilter[]
  sort: SearchSort
  pagination: SearchPagination
  facets: SearchFacet[]
  suggestions: boolean
  highlighting: boolean
}

export interface SearchFilter {
  field: string
  operator: FilterOperator
  value: any
  boost?: number
}

export interface SearchSort {
  field: string
  order: SortOrder
  boost?: number
}

export interface SearchPagination {
  page: number
  size: number
  offset: number
}

export interface SearchFacet {
  field: string
  size: number
  minCount: number
}

export interface SearchSuggestion {
  text: string
  score: number
  type: SuggestionType
  category?: string
  frequency: number
}

export interface HelpContext {
  page: string
  section?: string
  feature?: string
  userRole: string
  userLevel: ExperienceLevel
  previousActions: string[]
  currentTask?: string
  errorContext?: ErrorContext
  metadata: Record<string, any>
}

export interface ErrorContext {
  errorCode?: string
  errorMessage?: string
  stackTrace?: string
  userAgent?: string
  timestamp: string
}

export interface ContextualSuggestion {
  id: string
  type: SuggestionType
  title: string
  description: string
  url: string
  relevanceScore: number
  confidence: number
  category: string
  tags: string[]
  priority: SuggestionPriority
  triggers: SuggestionTrigger[]
  conditions: SuggestionCondition[]
}

export interface SuggestionTrigger {
  type: TriggerType
  value: string
  weight: number
}

export interface SuggestionCondition {
  field: string
  operator: string
  value: any
  required: boolean
}

export interface TroubleshootingGuide {
  id: string
  title: string
  description: string
  category: TroubleshootingCategory
  symptoms: Symptom[]
  diagnostics: DiagnosticStep[]
  solutions: Solution[]
  escalation: EscalationPath
  relatedArticles: string[]
  difficulty: DifficultyLevel
  estimatedTime: number
  successRate: number
  feedback: TroubleshootingFeedback
  createdAt: string
  updatedAt: string
  createdBy: string
}

export interface Symptom {
  id: string
  description: string
  severity: SymptomSeverity
  frequency: SymptomFrequency
  conditions: string[]
  indicators: string[]
}

export interface DiagnosticStep {
  id: string
  order: number
  title: string
  description: string
  type: DiagnosticType
  command?: string
  expectedOutput?: string
  troubleshooting?: string
  nextSteps: NextStep[]
  timeEstimate: number
}

export interface NextStep {
  condition: string
  action: string
  stepId?: string
  solutionId?: string
}

export interface Solution {
  id: string
  title: string
  description: string
  type: SolutionType
  steps: SolutionStep[]
  prerequisites: string[]
  warnings: string[]
  verification: VerificationStep[]
  rollback: RollbackStep[]
  difficulty: DifficultyLevel
  estimatedTime: number
  successRate: number
  riskLevel: RiskLevel
}

export interface SolutionStep {
  id: string
  order: number
  title: string
  description: string
  type: StepType
  command?: string
  parameters?: Record<string, any>
  expectedResult?: string
  troubleshooting?: string
  optional: boolean
  critical: boolean
}

export interface VerificationStep {
  id: string
  description: string
  command?: string
  expectedResult: string
  successCriteria: string[]
}

export interface RollbackStep {
  id: string
  order: number
  description: string
  command?: string
  conditions: string[]
  critical: boolean
}

export interface EscalationPath {
  levels: EscalationLevel[]
  contacts: EscalationContact[]
  procedures: string[]
  timeouts: number[]
}

export interface EscalationLevel {
  level: number
  title: string
  description: string
  contacts: string[]
  timeout: number
  conditions: string[]
}

export interface EscalationContact {
  id: string
  name: string
  role: string
  email: string
  phone?: string
  availability: string
  expertise: string[]
}

export interface TroubleshootingFeedback {
  totalAttempts: number
  successfulResolutions: number
  averageResolutionTime: number
  commonFailures: string[]
  improvements: string[]
  userRatings: number[]
}

export interface KnowledgeBaseStatistics {
  totalArticles: number
  publishedArticles: number
  draftArticles: number
  archivedArticles: number
  totalViews: number
  uniqueUsers: number
  averageRating: number
  searchQueries: number
  topArticles: PopularArticle[]
  topSearchTerms: PopularSearchTerm[]
  categoryStats: CategoryStatistics[]
  userEngagement: EngagementMetrics
  contentHealth: ContentHealthMetrics
}

export interface PopularArticle {
  id: string
  title: string
  views: number
  rating: number
  category: string
}

export interface PopularSearchTerm {
  term: string
  count: number
  results: number
  clickThrough: number
}

export interface CategoryStatistics {
  category: string
  articles: number
  views: number
  rating: number
  contributors: number
}

export interface EngagementMetrics {
  averageTimeOnPage: number
  bounceRate: number
  returnVisitors: number
  bookmarkRate: number
  shareRate: number
  commentRate: number
}

export interface ContentHealthMetrics {
  outdatedArticles: number
  lowRatedArticles: number
  orphanedArticles: number
  duplicateContent: number
  brokenLinks: number
  missingTranslations: number
}

// Enums and Union Types
export type ContentFormat = 'markdown' | 'html' | 'text' | 'wiki' | 'asciidoc'
export type ArticleCategory = 'tutorial' | 'guide' | 'reference' | 'troubleshooting' | 'faq' | 'api' | 'best-practices' | 'changelog'
export type ArticleType = 'article' | 'tutorial' | 'video' | 'interactive' | 'template' | 'checklist'
export type ArticleStatus = 'draft' | 'review' | 'published' | 'archived' | 'deprecated'
export type ArticleVisibility = 'public' | 'internal' | 'restricted' | 'private'
export type ContributorRole = 'author' | 'editor' | 'reviewer' | 'translator' | 'illustrator'
export type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert'
export type AudienceType = 'developer' | 'admin' | 'user' | 'manager' | 'support'
export type VersionStatus = 'draft' | 'pending' | 'approved' | 'published' | 'archived'
export type ChangeType = 'addition' | 'modification' | 'deletion' | 'restructure' | 'correction'
export type AttachmentType = 'image' | 'document' | 'video' | 'audio' | 'code' | 'data'
export type LinkType = 'internal' | 'external' | 'reference' | 'related' | 'source'
export type LinkStatus = 'active' | 'broken' | 'redirect' | 'unknown'
export type ReferenceType = 'book' | 'article' | 'website' | 'documentation' | 'video' | 'course'
export type TranslationStatus = 'pending' | 'in-progress' | 'completed' | 'reviewed' | 'published'
export type CommentStatus = 'pending' | 'approved' | 'rejected' | 'spam'
export type SuggestionType = 'improvement' | 'correction' | 'addition' | 'removal' | 'restructure'
export type SuggestionPriority = 'low' | 'medium' | 'high' | 'critical'
export type SuggestionStatus = 'open' | 'under-review' | 'approved' | 'implemented' | 'rejected'
export type ReportType = 'inappropriate' | 'spam' | 'copyright' | 'inaccurate' | 'outdated'
export type ReportStatus = 'open' | 'investigating' | 'resolved' | 'dismissed'
export type SearchResultType = 'article' | 'tutorial' | 'guide' | 'faq' | 'troubleshooting'
export type MatchType = 'exact' | 'partial' | 'fuzzy' | 'semantic' | 'phonetic'
export type FilterOperator = 'equals' | 'contains' | 'starts-with' | 'ends-with' | 'in' | 'range'
export type SortOrder = 'asc' | 'desc'
export type ExperienceLevel = 'novice' | 'beginner' | 'intermediate' | 'advanced' | 'expert'
export type TriggerType = 'page' | 'action' | 'error' | 'search' | 'time' | 'context'
export type TroubleshootingCategory = 'installation' | 'configuration' | 'performance' | 'error' | 'integration' | 'security'
export type SymptomSeverity = 'low' | 'medium' | 'high' | 'critical'
export type SymptomFrequency = 'rare' | 'occasional' | 'frequent' | 'constant'
export type DiagnosticType = 'check' | 'test' | 'command' | 'observation' | 'measurement'
export type SolutionType = 'fix' | 'workaround' | 'configuration' | 'upgrade' | 'replacement'
export type StepType = 'action' | 'command' | 'check' | 'wait' | 'decision'
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'

// Service Interfaces
export interface KnowledgeBaseService {
  getArticles(filters?: ArticleFilters): Promise<Article[]>
  getArticle(articleId: string): Promise<Article>
  createArticle(article: Omit<Article, 'id' | 'createdAt' | 'updatedAt'>): Promise<Article>
  updateArticle(articleId: string, updates: Partial<Article>): Promise<Article>
  deleteArticle(articleId: string): Promise<void>
  publishArticle(articleId: string): Promise<Article>
  archiveArticle(articleId: string): Promise<Article>
  searchArticles(query: SearchQuery): Promise<SearchResult[]>
  getSearchSuggestions(query: string): Promise<SearchSuggestion[]>
  getContextualSuggestions(context: HelpContext): Promise<ContextualSuggestion[]>
  getTroubleshootingGuides(filters?: TroubleshootingFilters): Promise<TroubleshootingGuide[]>
  getTroubleshootingGuide(guideId: string): Promise<TroubleshootingGuide>
  createTroubleshootingGuide(guide: Omit<TroubleshootingGuide, 'id' | 'createdAt' | 'updatedAt'>): Promise<TroubleshootingGuide>
  updateTroubleshootingGuide(guideId: string, updates: Partial<TroubleshootingGuide>): Promise<TroubleshootingGuide>
  deleteTroubleshootingGuide(guideId: string): Promise<void>
  rateArticle(articleId: string, userId: string, rating: number): Promise<void>
  addComment(articleId: string, userId: string, comment: string, rating?: number): Promise<FeedbackComment>
  reportArticle(articleId: string, userId: string, report: Omit<FeedbackReport, 'id' | 'createdAt'>): Promise<FeedbackReport>
  suggestImprovement(articleId: string, userId: string, suggestion: Omit<FeedbackSuggestion, 'id' | 'createdAt'>): Promise<FeedbackSuggestion>
  getArticleVersions(articleId: string): Promise<ArticleVersion[]>
  createArticleVersion(articleId: string, version: Omit<ArticleVersion, 'id' | 'createdAt'>): Promise<ArticleVersion>
  approveArticleVersion(versionId: string, approverId: string): Promise<ArticleVersion>
  getKnowledgeBaseStatistics(): Promise<KnowledgeBaseStatistics>
  getArticleAnalytics(articleId: string, period?: string): Promise<ArticleAnalytics>
  trackArticleView(articleId: string, userId?: string): Promise<void>
  bookmarkArticle(articleId: string, userId: string): Promise<void>
  unbookmarkArticle(articleId: string, userId: string): Promise<void>
  shareArticle(articleId: string, userId: string, platform: string): Promise<void>
  exportArticle(articleId: string, format: ExportFormat): Promise<string>
  importArticles(data: any, format: ImportFormat): Promise<ImportResult>
  validateLinks(articleId?: string): Promise<LinkValidationResult[]>
  generateSitemap(): Promise<SitemapEntry[]>
  getPopularContent(period?: string, limit?: number): Promise<PopularArticle[]>
  getRecentContent(limit?: number): Promise<Article[]>
  getRelatedArticles(articleId: string, limit?: number): Promise<Article[]>
  getArticlesByAuthor(authorId: string): Promise<Article[]>
  getArticlesByCategory(category: ArticleCategory): Promise<Article[]>
  getArticlesByTag(tag: string): Promise<Article[]>
}

export interface ArticleFilters {
  category?: ArticleCategory[]
  type?: ArticleType[]
  status?: ArticleStatus[]
  visibility?: ArticleVisibility[]
  author?: string
  tags?: string[]
  difficulty?: DifficultyLevel[]
  audience?: AudienceType[]
  dateRange?: {
    start: string
    end: string
  }
  search?: string
  minRating?: number
  hasAttachments?: boolean
  hasTranslations?: boolean
}

export interface TroubleshootingFilters {
  category?: TroubleshootingCategory[]
  difficulty?: DifficultyLevel[]
  symptoms?: string[]
  tags?: string[]
  author?: string
  dateRange?: {
    start: string
    end: string
  }
  search?: string
  minSuccessRate?: number
}

export interface ImportResult {
  success: boolean
  imported: number
  skipped: number
  errors: ImportError[]
  warnings: string[]
}

export interface ImportError {
  item: string
  error: string
  line?: number
}

export interface LinkValidationResult {
  articleId: string
  linkId: string
  url: string
  status: LinkStatus
  statusCode?: number
  error?: string
  checkedAt: string
}

export interface SitemapEntry {
  url: string
  lastModified: string
  changeFrequency: string
  priority: number
}

export type ExportFormat = 'pdf' | 'html' | 'markdown' | 'docx' | 'json'
export type ImportFormat = 'json' | 'csv' | 'xml' | 'confluence' | 'notion'

// Constants
export const ARTICLE_CATEGORIES: ArticleCategory[] = ['tutorial', 'guide', 'reference', 'troubleshooting', 'faq', 'api', 'best-practices', 'changelog']
export const ARTICLE_TYPES: ArticleType[] = ['article', 'tutorial', 'video', 'interactive', 'template', 'checklist']
export const ARTICLE_STATUSES: ArticleStatus[] = ['draft', 'review', 'published', 'archived', 'deprecated']
export const DIFFICULTY_LEVELS: DifficultyLevel[] = ['beginner', 'intermediate', 'advanced', 'expert']
export const AUDIENCE_TYPES: AudienceType[] = ['developer', 'admin', 'user', 'manager', 'support']

export const CATEGORY_COLORS = {
  tutorial: '#52c41a',
  guide: '#1890ff',
  reference: '#722ed1',
  troubleshooting: '#fa8c16',
  faq: '#13c2c2',
  api: '#eb2f96',
  'best-practices': '#f5222d',
  changelog: '#faad14'
} as const

export const STATUS_COLORS = {
  draft: 'orange',
  review: 'blue',
  published: 'green',
  archived: 'gray',
  deprecated: 'red'
} as const

export const DIFFICULTY_COLORS = {
  beginner: '#52c41a',
  intermediate: '#faad14',
  advanced: '#fa8c16',
  expert: '#f5222d'
} as const

export const DEFAULT_SEARCH_FILTERS: SearchFilter[] = [
  { field: 'status', operator: 'equals', value: 'published' },
  { field: 'visibility', operator: 'in', value: ['public', 'internal'] }
]

export const DEFAULT_SEARCH_SORT: SearchSort = {
  field: 'relevance',
  order: 'desc'
}

export const DEFAULT_PAGINATION: SearchPagination = {
  page: 1,
  size: 20,
  offset: 0
}