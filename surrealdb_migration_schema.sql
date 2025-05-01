-- ------------------------------
-- OPTION
-- ------------------------------

OPTION IMPORT;

-- ------------------------------
-- FUNCTIONS
-- ------------------------------

DEFINE FUNCTION fn::text_search($query_text: string, $match_count: int, $sources: bool, $show_notes: bool) {
LET $source_title_search = IF $sources { (SELECT id, title, search::highlight('`', '`', 1) AS content, id AS parent_id, math::max(search::score(1)) AS relevance FROM source WHERE title @1@ $query_text GROUP BY id) } ELSE { [] };
LET $source_embedding_search = IF $sources { (SELECT source.id AS id, source.title AS title, search::highlight('`', '`', 1) AS content, source.id AS parent_id, math::max(search::score(1)) AS relevance FROM source_embedding WHERE content @1@ $query_text GROUP BY id) } ELSE { [] };
LET $source_full_search = IF $sources { (SELECT id, title, search::highlight('`', '`', 1) AS content, id AS parent_id, math::max(search::score(1)) AS relevance FROM source WHERE full_text @1@ $query_text GROUP BY id) } ELSE { [] };
LET $source_insight_search = IF $sources { (SELECT id, insight_type + ' - ' + (source.title OR '') AS title, search::highlight('`', '`', 1) AS content, id AS parent_id, math::max(search::score(1)) AS relevance FROM source_insight WHERE content @1@ $query_text GROUP BY id) } ELSE { [] };
LET $note_title_search = IF $show_notes { (SELECT id, title, search::highlight('`', '`', 1) AS content, id AS parent_id, math::max(search::score(1)) AS relevance FROM note WHERE title @1@ $query_text GROUP BY id) } ELSE { [] };
LET $note_content_search = IF $show_notes { (SELECT id, title, search::highlight('`', '`', 1) AS content, id AS parent_id, math::max(search::score(1)) AS relevance FROM note WHERE content @1@ $query_text GROUP BY id) } ELSE { [] };
LET $source_chunk_results = array::union($source_embedding_search, $source_full_search);
LET $source_asset_results = array::union($source_title_search, $source_insight_search);
LET $source_results = array::union($source_chunk_results, $source_asset_results);
LET $note_results = array::union($note_title_search, $note_content_search);
LET $final_results = array::union($source_results, $note_results);
RETURN (SELECT id, parent_id, title, math::max(relevance) AS relevance FROM $final_results WHERE id != NONE GROUP BY id, parent_id, title ORDER BY relevance DESC
 LIMIT $match_count);
} PERMISSIONS FULL;
DEFINE FUNCTION fn::vector_search($query: array<float>, $match_count: int, $sources: bool, $show_notes: bool, $min_similarity: float) {
LET $source_embedding_search = IF $sources { (SELECT source.id AS id, source.title AS title, content, source.id AS parent_id, vector::similarity::cosine(embedding, $query) AS similarity FROM source_embedding WHERE vector::similarity::cosine(embedding, $query) >= $min_similarity ORDER BY similarity DESC
 LIMIT $match_count) } ELSE { [] };
LET $source_insight_search = IF $sources { (SELECT id, insight_type + ' - ' + (source.title OR '') AS title, content, source.id AS parent_id, vector::similarity::cosine(embedding, $query) AS similarity FROM source_insight WHERE vector::similarity::cosine(embedding, $query) >= $min_similarity ORDER BY similarity DESC
 LIMIT $match_count) } ELSE { [] };
LET $note_content_search = IF $show_notes { (SELECT id, title, content, id AS parent_id, vector::similarity::cosine(embedding, $query) AS similarity FROM note WHERE vector::similarity::cosine(embedding, $query) >= $min_similarity ORDER BY similarity DESC
 LIMIT $match_count) } ELSE { [] };
LET $all_results = array::union(array::union($source_embedding_search, $source_insight_search), $note_content_search);
RETURN (SELECT id, parent_id, title, math::max(similarity) AS similarity, array::flatten(content) AS matches FROM $all_results WHERE id != NONE GROUP BY id, parent_id, title ORDER BY similarity DESC
 LIMIT $match_count);
} PERMISSIONS FULL;

-- ------------------------------
-- ANALYZERS
-- ------------------------------

DEFINE ANALYZER my_analyzer TOKENIZERS BLANK,CLASS,CAMEL,PUNCT FILTERS SNOWBALL(ENGLISH),LOWERCASE;

-- ------------------------------
-- TABLE: _sbl_migrations
-- ------------------------------

DEFINE TABLE _sbl_migrations TYPE ANY SCHEMALESS PERMISSIONS NONE;




-- ------------------------------
-- TABLE DATA: _sbl_migrations
-- ------------------------------

INSERT [ { applied_at: d'2025-05-01T02:22:02.999383508Z', id: _sbl_migrations:1, version: 1 }, { applied_at: d'2025-05-01T02:22:03.035949528Z', id: _sbl_migrations:2, version: 2 }, { applied_at: d'2025-05-01T02:22:03.079071120Z', id: _sbl_migrations:3, version: 3 }, { applied_at: d'2025-05-01T02:22:03.114779361Z', id: _sbl_migrations:4, version: 4 }, { applied_at: d'2025-05-01T02:22:03.151810112Z', id: _sbl_migrations:5, version: 5 } ];

-- ------------------------------
-- TABLE: artifact
-- ------------------------------

DEFINE TABLE artifact TYPE RELATION IN note OUT notebook SCHEMALESS PERMISSIONS NONE;

DEFINE FIELD in ON artifact TYPE record<note> PERMISSIONS FULL;
DEFINE FIELD out ON artifact TYPE record<notebook> PERMISSIONS FULL;



-- ------------------------------
-- TABLE DATA: artifact
-- ------------------------------


-- ------------------------------
-- TABLE: chat_session
-- ------------------------------

DEFINE TABLE chat_session TYPE ANY SCHEMALESS PERMISSIONS NONE;




-- ------------------------------
-- TABLE DATA: chat_session
-- ------------------------------


-- ------------------------------
-- TABLE: model
-- ------------------------------

DEFINE TABLE model TYPE ANY SCHEMALESS PERMISSIONS NONE;




-- ------------------------------
-- TABLE DATA: model
-- ------------------------------

INSERT [ { created: '2025-05-01 02:22:03', id: model:7q9f2kdfjo1vk2iropv3, name: 'text-embedding-3-small', provider: 'openai', type: 'embedding', updated: '2025-05-01 02:22:03' }, { created: '2025-05-01 02:22:03', id: model:eok764jbnnutwa3r4vwj, name: 'whisper-1', provider: 'openai', type: 'speech_to_text', updated: '2025-05-01 02:22:03' }, { created: '2025-05-01 02:22:03', id: model:mrhcr45nw1hk37a3vy44, name: 'claude-3-7-sonnet-20250219', provider: 'anthropic', type: 'language', updated: '2025-05-01 02:22:03' } ];

-- ------------------------------
-- TABLE: note
-- ------------------------------

DEFINE TABLE note TYPE NORMAL SCHEMAFULL PERMISSIONS NONE;

DEFINE FIELD content ON note TYPE option<string> PERMISSIONS FULL;
DEFINE FIELD created ON note DEFAULT time::now() VALUE $before OR time::now() PERMISSIONS FULL;
DEFINE FIELD embedding ON note TYPE array<float> PERMISSIONS FULL;
DEFINE FIELD embedding[*] ON note TYPE float PERMISSIONS FULL;
DEFINE FIELD note_type ON note TYPE option<string> PERMISSIONS FULL;
DEFINE FIELD summary ON note TYPE option<string> PERMISSIONS FULL;
DEFINE FIELD title ON note TYPE option<string> PERMISSIONS FULL;
DEFINE FIELD updated ON note DEFAULT time::now() VALUE time::now() PERMISSIONS FULL;

DEFINE INDEX idx_note ON note FIELDS content SEARCH ANALYZER my_analyzer BM25(1.2,0.75) DOC_IDS_ORDER 100 DOC_LENGTHS_ORDER 100 POSTINGS_ORDER 100 TERMS_ORDER 100 DOC_IDS_CACHE 100 DOC_LENGTHS_CACHE 100 POSTINGS_CACHE 100 TERMS_CACHE 100 HIGHLIGHTS;
DEFINE INDEX idx_note_title ON note FIELDS title SEARCH ANALYZER my_analyzer BM25(1.2,0.75) DOC_IDS_ORDER 100 DOC_LENGTHS_ORDER 100 POSTINGS_ORDER 100 TERMS_ORDER 100 DOC_IDS_CACHE 100 DOC_LENGTHS_CACHE 100 POSTINGS_CACHE 100 TERMS_CACHE 100 HIGHLIGHTS;


-- ------------------------------
-- TABLE DATA: note
-- ------------------------------


-- ------------------------------
-- TABLE: notebook
-- ------------------------------

DEFINE TABLE notebook TYPE NORMAL SCHEMAFULL PERMISSIONS NONE;

DEFINE FIELD archived ON notebook TYPE option<bool> DEFAULT false PERMISSIONS FULL;
DEFINE FIELD created ON notebook DEFAULT time::now() VALUE $before OR time::now() PERMISSIONS FULL;
DEFINE FIELD description ON notebook TYPE option<string> PERMISSIONS FULL;
DEFINE FIELD name ON notebook TYPE option<string> PERMISSIONS FULL;
DEFINE FIELD updated ON notebook DEFAULT time::now() VALUE time::now() PERMISSIONS FULL;



-- ------------------------------
-- TABLE DATA: notebook
-- ------------------------------


-- ------------------------------
-- TABLE: open_notebook
-- ------------------------------

DEFINE TABLE open_notebook TYPE ANY SCHEMALESS PERMISSIONS NONE;




-- ------------------------------
-- TABLE DATA: open_notebook
-- ------------------------------

INSERT [ { default_chat_model: model:mrhcr45nw1hk37a3vy44, default_embedding_model: model:7q9f2kdfjo1vk2iropv3, default_speech_to_text_model: model:eok764jbnnutwa3r4vwj, default_transformation_model: model:mrhcr45nw1hk37a3vy44, id: open_notebook:default_models, large_context_model: model:mrhcr45nw1hk37a3vy44 }, { id: open_notebook:default_transformations, source_insights: ['Summarize'] } ];

-- ------------------------------
-- TABLE: podcast_config
-- ------------------------------

DEFINE TABLE podcast_config TYPE ANY SCHEMALESS PERMISSIONS NONE;




-- ------------------------------
-- TABLE DATA: podcast_config
-- ------------------------------


-- ------------------------------
-- TABLE: reference
-- ------------------------------

DEFINE TABLE reference TYPE RELATION IN source OUT notebook SCHEMALESS PERMISSIONS NONE;

DEFINE FIELD in ON reference TYPE record<source> PERMISSIONS FULL;
DEFINE FIELD out ON reference TYPE record<notebook> PERMISSIONS FULL;



-- ------------------------------
-- TABLE DATA: reference
-- ------------------------------


-- ------------------------------
-- TABLE: refers_to
-- ------------------------------

DEFINE TABLE refers_to TYPE RELATION IN chat_session OUT notebook SCHEMALESS PERMISSIONS NONE;

DEFINE FIELD in ON refers_to TYPE record<chat_session> PERMISSIONS FULL;
DEFINE FIELD out ON refers_to TYPE record<notebook> PERMISSIONS FULL;



-- ------------------------------
-- TABLE DATA: refers_to
-- ------------------------------


-- ------------------------------
-- TABLE: source
-- ------------------------------

DEFINE TABLE source TYPE NORMAL SCHEMAFULL PERMISSIONS NONE;

DEFINE FIELD asset ON source FLEXIBLE TYPE option<object> PERMISSIONS FULL;
DEFINE FIELD created ON source DEFAULT time::now() VALUE $before OR time::now() PERMISSIONS FULL;
DEFINE FIELD full_text ON source TYPE option<string> PERMISSIONS FULL;
DEFINE FIELD title ON source TYPE option<string> PERMISSIONS FULL;
DEFINE FIELD topics ON source TYPE option<array<string>> PERMISSIONS FULL;
DEFINE FIELD topics[*] ON source TYPE string PERMISSIONS FULL;
DEFINE FIELD updated ON source DEFAULT time::now() VALUE time::now() PERMISSIONS FULL;

DEFINE INDEX idx_source_full_text ON source FIELDS full_text SEARCH ANALYZER my_analyzer BM25(1.2,0.75) DOC_IDS_ORDER 100 DOC_LENGTHS_ORDER 100 POSTINGS_ORDER 100 TERMS_ORDER 100 DOC_IDS_CACHE 100 DOC_LENGTHS_CACHE 100 POSTINGS_CACHE 100 TERMS_CACHE 100 HIGHLIGHTS;
DEFINE INDEX idx_source_title ON source FIELDS title SEARCH ANALYZER my_analyzer BM25(1.2,0.75) DOC_IDS_ORDER 100 DOC_LENGTHS_ORDER 100 POSTINGS_ORDER 100 TERMS_ORDER 100 DOC_IDS_CACHE 100 DOC_LENGTHS_CACHE 100 POSTINGS_CACHE 100 TERMS_CACHE 100 HIGHLIGHTS;

DEFINE EVENT source_delete ON source WHEN ($after == NONE) THEN {
DELETE source_embedding WHERE source == $before.id;
DELETE source_insight WHERE source == $before.id;
};

-- ------------------------------
-- TABLE DATA: source
-- ------------------------------


-- ------------------------------
-- TABLE: source_embedding
-- ------------------------------

DEFINE TABLE source_embedding TYPE NORMAL SCHEMAFULL PERMISSIONS NONE;

DEFINE FIELD content ON source_embedding TYPE string PERMISSIONS FULL;
DEFINE FIELD embedding ON source_embedding TYPE array<float> PERMISSIONS FULL;
DEFINE FIELD embedding[*] ON source_embedding TYPE float PERMISSIONS FULL;
DEFINE FIELD order ON source_embedding TYPE int PERMISSIONS FULL;
DEFINE FIELD source ON source_embedding TYPE record<source> PERMISSIONS FULL;

DEFINE INDEX idx_source_embed_chunk ON source_embedding FIELDS content SEARCH ANALYZER my_analyzer BM25(1.2,0.75) DOC_IDS_ORDER 100 DOC_LENGTHS_ORDER 100 POSTINGS_ORDER 100 TERMS_ORDER 100 DOC_IDS_CACHE 100 DOC_LENGTHS_CACHE 100 POSTINGS_CACHE 100 TERMS_CACHE 100 HIGHLIGHTS;


-- ------------------------------
-- TABLE DATA: source_embedding
-- ------------------------------


-- ------------------------------
-- TABLE: source_insight
-- ------------------------------

DEFINE TABLE source_insight TYPE NORMAL SCHEMAFULL PERMISSIONS NONE;

DEFINE FIELD content ON source_insight TYPE string PERMISSIONS FULL;
DEFINE FIELD embedding ON source_insight TYPE array<float> PERMISSIONS FULL;
DEFINE FIELD embedding[*] ON source_insight TYPE float PERMISSIONS FULL;
DEFINE FIELD insight_type ON source_insight TYPE string PERMISSIONS FULL;
DEFINE FIELD source ON source_insight TYPE record<source> PERMISSIONS FULL;

DEFINE INDEX idx_source_insight ON source_insight FIELDS content SEARCH ANALYZER my_analyzer BM25(1.2,0.75) DOC_IDS_ORDER 100 DOC_LENGTHS_ORDER 100 POSTINGS_ORDER 100 TERMS_ORDER 100 DOC_IDS_CACHE 100 DOC_LENGTHS_CACHE 100 POSTINGS_CACHE 100 TERMS_CACHE 100 HIGHLIGHTS;


-- ------------------------------
-- TABLE DATA: source_insight
-- ------------------------------


