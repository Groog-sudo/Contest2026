/**
 * @typedef {Object} LeadRegistrationRequest
 * @property {string} student_name
 * @property {string} phone_number
 * @property {string} course_interest
 * @property {string} learning_goal
 * @property {string | null | undefined} [preferred_call_time]
 * @property {boolean} consent_to_call
 */

/**
 * @typedef {Object} LeadRegistrationResponse
 * @property {string} lead_id
 * @property {'captured'} status
 * @property {string} next_action
 */

/**
 * @typedef {Object} CallSourceItem
 * @property {string} id
 * @property {string} title
 * @property {number | undefined} [score]
 */

/**
 * @typedef {Object} CallRequest
 * @property {string} lead_id
 * @property {string} student_name
 * @property {string} phone_number
 * @property {string} course_interest
 * @property {string} student_question
 * @property {number | undefined} [top_k]
 */

/**
 * @typedef {Object} CallRequestResponse
 * @property {string} call_id
 * @property {'drafted' | 'script_ready' | 'queued'} status
 * @property {string} script_preview
 * @property {CallSourceItem[]} sources
 * @property {string} next_step
 */

/**
 * @typedef {Object} UploadDocumentResponse
 * @property {string} document_id
 * @property {'accepted' | 'knowledge_base_pending'} status
 */

/**
 * @typedef {Object} CallTranscriptTurn
 * @property {'student' | 'ai' | 'counselor'} speaker
 * @property {string} utterance
 */

/**
 * @typedef {Object} CallTranscriptIngestRequest
 * @property {string} call_id
 * @property {string} lead_id
 * @property {string | undefined} [recording_url]
 * @property {string | undefined} [transcript_text]
 * @property {CallTranscriptTurn[] | undefined} [turns]
 */

/**
 * @typedef {Object} CallTranscriptIngestResponse
 * @property {string} transcript_id
 * @property {'stored'} status
 * @property {number} saved_turns
 * @property {string} summary
 */

/**
 * @typedef {Object} TTSPreviewRequest
 * @property {string} script
 * @property {string | undefined} [voice]
 */

/**
 * @typedef {Object} TTSPreviewResponse
 * @property {'generated'} status
 * @property {string} provider
 * @property {string} voice
 * @property {string} audio_url
 * @property {string} mime_type
 */

/**
 * @typedef {Object} SkillAnswer
 * @property {string} area
 * @property {number} score
 */

/**
 * @typedef {Object} LevelAssessmentRequest
 * @property {string} lead_id
 * @property {SkillAnswer[]} answers
 * @property {string | undefined} [additional_context]
 */

/**
 * @typedef {Object} LevelAssessmentResponse
 * @property {string} assessment_id
 * @property {'beginner' | 'intermediate' | 'advanced'} level
 * @property {number} score
 * @property {string} recommended_course
 * @property {string} mentoring_plan
 * @property {string[]} rag_context_ids
 */

/**
 * @typedef {Object} RecordingUploadResponse
 * @property {string} recording_id
 * @property {'queued'} status
 * @property {string} object_key
 * @property {string} storage_url
 * @property {string} queue_task_id
 */

/**
 * @typedef {Object} DashboardSeriesPoint
 * @property {string} date
 * @property {number} leads
 * @property {number} calls
 * @property {number} assessments
 */

/**
 * @typedef {Object} DashboardMetricsResponse
 * @property {number} total_leads
 * @property {number} leads_with_calls
 * @property {number} leads_with_assessments
 * @property {number} conversion_rate
 * @property {number} completion_rate
 * @property {number} avg_assessment_score
 * @property {number} queued_tasks
 * @property {number} processing_tasks
 * @property {number} failed_tasks
 * @property {number} period_days
 * @property {DashboardSeriesPoint[]} series
 */

/**
 * @typedef {Object} QueueTaskItem
 * @property {string} task_id
 * @property {string} task_type
 * @property {'queued' | 'processing' | 'done' | 'failed'} status
 * @property {number} attempts
 * @property {Object} payload
 * @property {Object | null | undefined} [result]
 * @property {string | null | undefined} [error_message]
 * @property {string} created_at
 * @property {string} updated_at
 */

/**
 * @typedef {Object} QueueTaskListResponse
 * @property {QueueTaskItem[]} items
 */

/**
 * @typedef {Object} QueueTaskProcessResponse
 * @property {string} task_id
 * @property {'done' | 'failed'} status
 * @property {Object | null | undefined} [result]
 * @property {string | null | undefined} [error_message]
 * @property {boolean | undefined} [retry_queued]
 */

/**
 * @typedef {Object} QueueWorkerRunResponse
 * @property {number} requested_limit
 * @property {number} processed
 * @property {number} succeeded
 * @property {number} failed
 * @property {number} requeued
 */

export {};
