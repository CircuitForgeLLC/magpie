-- Migration 021: Opportunity assignment + posting account
-- assigned_to: which team member is responsible for this opportunity.
-- post_as: which team account to use when auto-posting.
-- These are separate: Alan may be assigned to review but post as CF official.
ALTER TABLE opportunities ADD COLUMN assigned_to INTEGER REFERENCES team_accounts(id);
ALTER TABLE opportunities ADD COLUMN post_as     INTEGER REFERENCES team_accounts(id);
