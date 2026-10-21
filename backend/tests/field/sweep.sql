-- Field test, tier 0: invariant counts over a live database. Read-only.
-- Run each statement through the Render Postgres connector, or: psql "$DATABASE_URL" -f sweep.sql
-- Ids are the invariants in invariants.py. Paste results into work/FIELD-TESTS.md.

-- totals
select (select count(*) from users) users, (select count(*) from criteria) criteria,
       (select count(*) from runs) runs, (select count(*) from events) events, now();

-- I1 past dates. past_when_stored = the date was already gone when the pipeline kept it (pipeline bug);
-- past_now = aged out since (the feed never expires, issue #78); same_day_date_only = underway today.
select status,
       count(*) filter (where left(date_time,10) < left(created_at::text,10)) past_when_stored,
       count(*) filter (where left(date_time,10) < left(created_at::text,10) and coalesce(decided_by,'auto')<>'user') past_when_stored_auto,
       count(*) filter (where left(date_time,10) < to_char(now(),'YYYY-MM-DD')) past_now,
       count(*) filter (where length(date_time)=10 and left(date_time,10) = left(created_at::text,10)) same_day_date_only,
       count(*) filter (where date_time !~ '^\d{4}-\d{2}-\d{2}') unparsed,
       count(*) total
from events where status in ('accepted','queued') group by status;

-- I2 country spread per user. Read against the criteria text: a named place with other countries = violation.
select u.username, left(c.text,45) criteria,
       string_agg(e.country||':'||e.n, ' ' order by e.n desc) countries
from users u join criteria c on c.user_id=u.id
join (select user_id, country, count(*) n from events where status in ('accepted','queued') group by 1,2) e on e.user_id=u.id
group by 1,2 order by 1;

-- I3 hedged auto-accepts
select count(*) n, count(distinct user_id) users
from events where status='accepted' and coalesce(decided_by,'auto')<>'user'
  and score_reason ~* '(not confirmed|unconfirmed|rather than|no place|no city|no location|no date|not specified|although|though|however|but it is in|outside)';

-- I4 counters: the run report against the events table for that run
with r as (select id, stage_counts::jsonb c from runs where stage_counts is not null),
     ev as (select run_id, count(*) filter (where status in ('accepted','queued','rejected')) n from events group by run_id)
select count(*) runs_with_counts,
       count(*) filter (where coalesce((c->>'accepted')::int,0)+coalesce((c->>'queued')::int,0)+coalesce((c->>'rejected')::int,0) <> coalesce((c->>'events_judged')::int,0)) judged_mismatch,
       count(*) filter (where coalesce((c->>'events_judged')::int,0) <> coalesce(ev.n,0)) report_vs_table
from r left join ev on ev.run_id=r.id;

-- I6 link and time quality on kept events
select status,
       count(*) filter (where link ~ '^https?://[^/]+/?$') root_link,
       count(*) filter (where link ~* '(/search|[?&]q=|/events/?$|/calendar/?$|/agenda/?$|/whats-on/?$)') listing_link,
       count(*) filter (where length(date_time)=10 and end_time is null) no_time,
       count(*) total
from events where status in ('accepted','queued') group by status;

-- I7 duplicates among kept events
select count(*) dup_groups, sum(n-1) extra_events from (
  select user_id, lower(regexp_replace(title,'[^a-zA-Z0-9]+',' ','g')) t, left(date_time,10) d, count(*) n
  from events where status in ('accepted','queued') group by 1,2,3 having count(*)>1) s;

-- I10 run errors as the user would see them
select left(error,90) err, stopped_at_stage, count(*) from runs
where error is not null or stopped_at_stage is not null group by 1,2 order by 3 desc limit 20;
