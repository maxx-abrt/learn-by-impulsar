import asyncio        
import streamlit as st     
import time
from functools import partial
from datetime import datetime

def clock(field, name, starttime):
    """Print a time in a field"""
    tdelta =  datetime.now().replace(microsecond=0) - starttime.replace(microsecond=0)
    minutes, seconds = divmod(int(tdelta.total_seconds()), 60)      
    hours, minutes = divmod(minutes, 60)                                                                       
    field.metric(name, f"{hours}:{minutes:02d}:{seconds:02d}")

async def run_jobs(job_list):
    while True:
        for job in job_list:
            job()
        # Not sure why asyncio.sleep was used here...
        time.sleep(0.1)

col1, col2 = st.columns(2)
# Placeholder Fields for Timers
with col1:
    all_tasks = st.empty()
with col2:
    ph = st.empty()

jobs = []

# Jobs are queued for the fields
jobs.append(partial(clock, all_tasks, "foo", datetime(2023, 12, 28, 14)))
jobs.append(partial(clock, ph, "baz", datetime(2023, 12, 28, 16)))

if jobs:
    # not sure why asyncio is actually needed - a normal function works as well.
    asyncio.run(run_jobs(jobs))