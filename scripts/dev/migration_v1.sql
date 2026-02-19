-- 1. Add job_type column to nexus_jobs
ALTER TABLE nexus_jobs 
ADD COLUMN IF NOT EXISTS job_type text;

-- 2. Add tags column to automation_contacts
ALTER TABLE automation_contacts 
ADD COLUMN IF NOT EXISTS tags text[] DEFAULT '{}';

-- 3. Create index for performance (optional but good)
CREATE INDEX IF NOT EXISTS idx_nexus_jobs_job_type ON nexus_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_contacts_tags ON automation_contacts USING GIN(tags);

-- 4. Initial tagging of key users (Idempotent)
-- Graziela (Tax + Director equivalent)
UPDATE automation_contacts 
SET tags = array_append(tags, 'tax') 
WHERE name ILIKE '%Graziela%' AND NOT ('tax' = ANY(tags));

UPDATE automation_contacts 
SET tags = array_append(tags, 'director') 
WHERE name ILIKE '%Graziela%' AND NOT ('director' = ANY(tags));

-- Mauricio (Corporate + Director equivalent)
UPDATE automation_contacts 
SET tags = array_append(tags, 'corporate') 
WHERE name ILIKE '%Mauricio%' AND NOT ('corporate' = ANY(tags));

UPDATE automation_contacts 
SET tags = array_append(tags, 'director') 
WHERE name ILIKE '%Mauricio%' AND NOT ('director' = ANY(tags));

-- Nicholas (Director)
UPDATE automation_contacts 
SET tags = array_append(tags, 'director') 
WHERE name ILIKE '%Nicholas%' AND NOT ('director' = ANY(tags));

-- José Carlos (Director)
UPDATE automation_contacts 
SET tags = array_append(tags, 'director') 
WHERE name ILIKE '%José Carlos%' AND NOT ('director' = ANY(tags));

-- Yuri (Director)
UPDATE automation_contacts 
SET tags = array_append(tags, 'director') 
WHERE name ILIKE '%Yuri%' AND NOT ('director' = ANY(tags));
