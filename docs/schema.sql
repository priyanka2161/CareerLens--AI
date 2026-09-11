-- Generated initial PostgreSQL schema. Use migrations for subsequent upgrades.


CREATE TABLE skills (
	name VARCHAR NOT NULL, 
	category VARCHAR NOT NULL, 
	aliases JSON NOT NULL, 
	PRIMARY KEY (name)
)

;


CREATE TABLE users (
	id VARCHAR NOT NULL, 
	token_hash VARCHAR NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id)
)

;

CREATE UNIQUE INDEX ix_users_token_hash ON users (token_hash);


CREATE TABLE jobs (
	id VARCHAR NOT NULL, 
	user_id VARCHAR, 
	title VARCHAR NOT NULL, 
	company VARCHAR, 
	location VARCHAR, 
	structured JSON NOT NULL, 
	salary_min FLOAT, 
	salary_max FLOAT, 
	currency VARCHAR, 
	salary_period VARCHAR, 
	source VARCHAR, 
	is_sample BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_jobs_user_id ON jobs (user_id);

CREATE INDEX ix_jobs_location ON jobs (location);

CREATE INDEX ix_jobs_title ON jobs (title);


CREATE TABLE resumes (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	structured JSON NOT NULL, 
	filename VARCHAR NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_resumes_user_id ON resumes (user_id);


CREATE TABLE job_skills (
	job_id VARCHAR NOT NULL, 
	skill_name VARCHAR NOT NULL, 
	required BOOLEAN NOT NULL, 
	PRIMARY KEY (job_id, skill_name), 
	FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE, 
	FOREIGN KEY(skill_name) REFERENCES skills (name)
)

;

CREATE INDEX ix_job_skill_name ON job_skills (skill_name);


CREATE TABLE match_results (
	id VARCHAR NOT NULL, 
	resume_id VARCHAR NOT NULL, 
	job_id VARCHAR NOT NULL, 
	result JSON NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (resume_id, job_id), 
	FOREIGN KEY(resume_id) REFERENCES resumes (id) ON DELETE CASCADE, 
	FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_match_results_resume_id ON match_results (resume_id);

CREATE INDEX ix_match_results_job_id ON match_results (job_id);


CREATE TABLE recommendations (
	id VARCHAR NOT NULL, 
	resume_id VARCHAR NOT NULL, 
	role_filter VARCHAR NOT NULL, 
	data JSON NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (resume_id, role_filter), 
	FOREIGN KEY(resume_id) REFERENCES resumes (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_recommendations_resume_id ON recommendations (resume_id);


CREATE TABLE resume_skills (
	resume_id VARCHAR NOT NULL, 
	skill_name VARCHAR NOT NULL, 
	evidence VARCHAR NOT NULL, 
	PRIMARY KEY (resume_id, skill_name), 
	FOREIGN KEY(resume_id) REFERENCES resumes (id) ON DELETE CASCADE, 
	FOREIGN KEY(skill_name) REFERENCES skills (name)
)

;

CREATE INDEX ix_resume_skill_name ON resume_skills (skill_name);