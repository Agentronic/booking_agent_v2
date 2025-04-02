We are going to build an extremely simplistic calendar slot booking subsystem.
This system will support just four operations:

* next_available_slot(after_date_time, duration)
  this returns the next date+time after the given date/time, where there is an available slot that is at least duration minutes
  
* is_slot_available(date, time, duration)
  this returns true if the entire time from date+time, lasting duration minutes, is available
  false otherwise
  
* book_slot(date, start_time, duration, client_id, service_name)
  this marks the slot at the given date, time, and duration, as being booked by 
  user whose id is client_id for the named service. 
  - service_name is an arbitrary string up to 100 characters
  - client_id is an arbitrary string, up to 32 characters (in practice, these will be phone numbers)
  
* release_slot(date, start_time)
  - releases the booking at date+time, regardless of who had it, for what, and how long 

durations are always in minutes, integer, and multiple of 15
dates are always yyyy-mm-dd
times are always hh:mm

Storage will be SQLite embedded database.
Minimally, there will be a single table with columns:
date, start_time, duration_minutes, customer_id, service_name

sample data:

If storing end_time instead of, or in addition to, duration, makes implementation easer, go ahead and do that.
In fact, make the storage whatever you want it to be to minimize code complexity e.g. by leveraging datatabase capabilities.

**This is all throw-away until we hook into external calendar services.**
- Use whatever column data types make implementation of the access methods easiest.
- *Do not even consider optimization*. Full table scan on every operation is perfectly fine, simplest and most compact code possible is te goal.
- Don't write a lot of corner case handling code.
- There is no concept of time zones, DLS, leap years, any irregularity whatsoever
- In fact, if it makes implementation easier, you can treat all months as if they have 30 days exactly. If it does not make things easier, don't do that.

Write this code in Python in a single file, `slot_calendar.py`
Step 1 is to create the access methods, but the do nothing.
  I will review the stubs before you proceed to next step
Step 2 is to create the unit tests, which should fail because the methods are still just stubs
  The unit test should not mock db access; they should test end to end; start with wiping db; use separate db for tests vs runtime
  I will review the test cases before you proceed to the next step
Step 3 is to write the actual methods
Iterate running the tests and modifying code until all the tests pass
