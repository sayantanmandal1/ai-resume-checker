SELECT id,
       filename,
       suggested_job_role,
       resume_summary,
       skills_present,
       skills_missing,
       score_out_of_100,
       status
FROM public.resume_reports
LIMIT 1000;