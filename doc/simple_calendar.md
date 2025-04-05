We are going to build an extremely simplistic calendar slot booking subsystem.
This will support just five operations

* `slots_available_on_day(date, duration)`
  Returns a list of available slots (times) on the given day and of at least the given duration. 
  These can ovelap, e.g. if the entire day is open, asking for a 1hr slot should return 9am, 9:30am, 10am...
  Slots are aligned to 30min, though bookings can be multipls of 15 (so as to not overwhelm the user with
  too many options).
  
  Subsequent enhancement, maybe:
  **If**
    - the requested slot is a multiple of :15, *not* a multiple of :30, and
    - there is already a booking that ends at XX:15 or XX:45, and
    - that booking is immediately followed by availability satisfyig the request
  **Then** a slot immediately after the existing booking (at XX:15 or XX:45) is offered, 
  *instead of* the *following* XX:30 or (XX+01):00 which would be normally be offered
  This tries to avoid ending up with too many "dead" unbookable slots of :15
  while still satisfying the overriding goal of limiting user options to XX:00 and XX:30 most of the time

* `next_available_slot(after_date_time, duration)`
  Returns the next date+time after the given date/time, where there is an available slot that is at least duration minutes
  
* `is_slot_available(date, time, duration)`
  Returns true if the entire time from date+time, lasting duration minutes, is available
  false otherwise. Note that this may return True for some slot even if slots_available_on_day 
  did not offer this slot, because that method "snaps" to :30 and this one "snaps" to :15.
  
* `book_slot(date, start_time, duration, client_id, service_name)`
  Marks the slot at the given date, time, and duration, as being booked by 
  user whose id is client_id for the named service. 
  Returns a **booking_id**
  - service_name is an arbitrary string up to 100 characters
  - client_id is an arbitrary string, up to 32 characters (in practice, these will be phone numbers)
  - booking_id return value is some sequence generator
  raises specific exception if the slot is not available
  
* `cancel_booking(booking_id)`
  Deletes the booking releasing the slot

Durations are always in minutes, integer, and multiple of 15
Dates are always yyyy-mm-dd
Rimes are always hh:mm

Storage will be SQLite embedded database.
Minimally, there will be a single table with columns:
date, start_time, duration_minutes, customer_id, service_name

If storing end_time instead of, or in addition to, duration, makes implementation easer, go ahead and do that.
In fact, make the storage whatever you want it to be to minimize code complexity e.g. by leveraging datatabase capabilities.

**This is all throw-away until we hook into external calendar services.**
- Use whatever column data types make implementation of the access methods easiest.
- **Do not even consider optimization**. Full table scan on every operation is perfectly fine, simplest and most compact code possible is te goal.
- Don't write a lot of corner case handling code.
- There is no concept of time zones, DLS, leap years, any irregularity whatsoever
- In fact, if it makes implementation easier, you can treat all months as if they have 30 days exactly. If it does not make things easier, don't do that.

Write this code in Python in a single file, `slot_calendar.py`
- **Step 1** is to create the access methods, but the do nothing.
  I will review the stubs before you proceed to next step
- **Step 2** is to create the unit tests, which should fail because the methods are still just stubs
  The unit test should not mock db access; they should test end to end; start with wiping db; use separate db for tests vs runtime
  I will review the test cases before you proceed to the next step
- **Step 3** is to write the actual methods
  Iterate running the tests and modifying code until all the tests pass
