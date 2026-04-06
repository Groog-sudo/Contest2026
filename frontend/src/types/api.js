/**
 * @typedef {Object} SourceItem
 * @property {string} id
 * @property {string} title
 * @property {number | undefined} [score]
 */

/**
 * @typedef {Object} ChatQueryRequest
 * @property {string} question
 * @property {number | undefined} [top_k]
 */

/**
 * @typedef {Object} ChatQueryResponse
 * @property {string} answer
 * @property {SourceItem[]} sources
 */

/**
 * @typedef {Object} UploadDocumentResponse
 * @property {string} document_id
 * @property {'accepted' | 'unconfigured'} status
 */

export {};
