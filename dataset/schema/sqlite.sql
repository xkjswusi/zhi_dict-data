PRAGMA user_version = 3;
CREATE TABLE aliases (entry_id TEXT NOT NULL, seq INTEGER NOT NULL, kind TEXT NOT NULL,
  from_sense_uid TEXT, target_entry_id TEXT, target_trad TEXT, target_simp TEXT,
  target_pinyin TEXT, resolved INTEGER NOT NULL, PRIMARY KEY (entry_id, seq)) WITHOUT ROWID;
CREATE TABLE classifiers (sense_uid TEXT NOT NULL, seq INTEGER NOT NULL, trad TEXT NOT NULL,
  simp TEXT, pinyin TEXT NOT NULL, PRIMARY KEY (sense_uid, seq)) WITHOUT ROWID;
CREATE TABLE common_words (sense_uid TEXT NOT NULL, seq INTEGER NOT NULL, trad TEXT NOT NULL,
  simp TEXT, pinyin TEXT NOT NULL, target_entry_id TEXT, resolved INTEGER NOT NULL,
  ex_trad TEXT NOT NULL, ex_simp TEXT, ex_realized TEXT NOT NULL, ex_spans TEXT NOT NULL,
  ex_shows TEXT, ex_shows_simp TEXT, PRIMARY KEY (sense_uid, seq)) WITHOUT ROWID;
CREATE TABLE entries (entry_id TEXT PRIMARY KEY, trad TEXT NOT NULL, simp TEXT NOT NULL,
  pinyin TEXT NOT NULL, content_status TEXT NOT NULL, rank INTEGER NOT NULL,
  zipf_subtlex REAL, review_status TEXT NOT NULL, adjudication TEXT,
  batch TEXT NOT NULL, prov_id INTEGER NOT NULL);
CREATE TABLE examples (sense_uid TEXT NOT NULL, seq INTEGER NOT NULL, trad TEXT NOT NULL,
  simp TEXT, realized TEXT NOT NULL, spans TEXT NOT NULL, shows TEXT, shows_simp TEXT,
  PRIMARY KEY (sense_uid, seq)) WITHOUT ROWID;
CREATE TABLE glosses (entry_id TEXT NOT NULL, idx INTEGER NOT NULL, text TEXT NOT NULL,
  PRIMARY KEY (entry_id, idx)) WITHOUT ROWID;
CREATE TABLE house_entries (entry_id TEXT PRIMARY KEY) WITHOUT ROWID;
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE pron_variants (entry_id TEXT NOT NULL, seq INTEGER NOT NULL, kind TEXT NOT NULL,
  pinyin TEXT NOT NULL, applies_to TEXT, PRIMARY KEY (entry_id, seq)) WITHOUT ROWID;
CREATE TABLE provenance (prov_id INTEGER PRIMARY KEY, model TEXT NOT NULL,
  method TEXT NOT NULL, generated_on TEXT NOT NULL, prompts TEXT NOT NULL);
CREATE TABLE search_hanzi (entry_id TEXT NOT NULL, form TEXT NOT NULL);
CREATE TABLE search_pinyin (entry_id TEXT NOT NULL, toned TEXT NOT NULL, plain TEXT NOT NULL,
  kind TEXT NOT NULL);
CREATE TABLE senses (sense_uid TEXT PRIMARY KEY, entry_id TEXT NOT NULL,
  ordinal INTEGER NOT NULL, sense_kind TEXT NOT NULL, pos TEXT NOT NULL,
  pos_simp TEXT NOT NULL, tags TEXT NOT NULL, register TEXT NOT NULL, domain TEXT NOT NULL,
  def_trad TEXT, def_simp TEXT, expl_trad TEXT, expl_simp TEXT, exemption TEXT,
  sgi TEXT NOT NULL, prompt_id TEXT, review_status TEXT NOT NULL, adjudication TEXT,
  edits TEXT NOT NULL, entity TEXT, dates TEXT, source_entry_id TEXT NOT NULL,
  prov_id INTEGER NOT NULL) WITHOUT ROWID;
CREATE TABLE xrefs (sense_uid TEXT NOT NULL, seq INTEGER NOT NULL, target_entry_id TEXT,
  target_trad TEXT NOT NULL, target_simp TEXT, target_pinyin TEXT NOT NULL,
  PRIMARY KEY (sense_uid, seq)) WITHOUT ROWID;
CREATE INDEX idx_entries_rank ON entries(rank);
CREATE INDEX idx_entries_simp ON entries(simp);
CREATE INDEX idx_entries_trad ON entries(trad);
CREATE INDEX idx_senses_entry ON senses(entry_id, ordinal);
CREATE INDEX idx_sh_form ON search_hanzi(form);
CREATE INDEX idx_sp_plain ON search_pinyin(plain);
CREATE INDEX idx_sp_toned ON search_pinyin(toned);
