OppiaMobile Android App Change Log
====================================

To see the upcoming feature developments and bug fixes, please refer to the `monthly milestones on GitHub <https://github.com/DigitalCampus/oppia-mobile-android/milestones>`_


.. _appv60:

v60 (6.1.0) - Not yet released 
--------------------------------------

.. note:: 
	This releases implements a properties configuration file, eg for the Mint API key and other settings for the app. 
	
* 527: Improved error messages when connecting to Oppia server - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/527
* 510: Invalidate user apiKey? - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/510
* 526: In quiz activity - if user has passed then show option to continue rather than retake - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/526
* 459: Allow max no attempts for quizzes - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/459
* 555: ListPreference requires an entries array and an entryValues array - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/555
* 552: Error on logging in : android.view.WindowLeaked - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/552
* 480: How to pre-load accounts onto the device - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/480
* 559: java.lang.IllegalStateException: Activity has been destroyed - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/559
* 477: Look at what would be needed to allow categories of courses - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/477
* 564: App shuts down when having installed a course by copying onto the sd card - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/564
* 549: Adding BugSense/Mint API key in non-Git file - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/549

.. _appv59:

v59 (6.0.2) - Released 7 May 2016
--------------------------------------

* Hotfix for video player

.. _appv58:

v58 (6.0.1) - Released 6 May 2016
--------------------------------------

* 490: Add option to show the logged in user - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/490
* 421: context menu of the main activity into a drawer - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/421
* 360: Look at how to reorganise menu options - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/360
* 538: Add mp3 as supported file type - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/538
* 338: On download courses page if no connection then close activity too - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/338
* 533: Update drawer header so the logo is pulled from the one specified for the app - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/533 
* 529: Show message when no tags/courses are available - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/529
* 534: Display message in scorecard if no courses installed - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/534
* 540: Occassional Null Pointer Exception on UIUtils.java:155 - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/540
* 514: Copy in the mquiz-jar classes - rather than having as separate jar - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/514
* 531: Permissions management in Android M - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/531

.. note:: 
	Starting with the release of the OppiaMobile Android App v57 (6.0.0), we will be moving to using Android Studio as the 
	supported development environment. This is an important note since the project structure will change significantly.


.. _appv57:

v57 (6.0.0) - Released skipped
--------------------------------------

Release skipped since we found some more issues with supporting SD cards in Android v4.4.2, this has been fixed in 
release v58 above.


.. _appv56:

v56 (5.5.0) - released 21 March 2016
--------------------------------------

* 473: Add options for display or not for the menu options - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/473
* 418: Not connecting to get course download list - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/418
* 463: Download media message not showing even when new courses are installed - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/463
* 470: NullPointer causes crash on start up - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/470
* 472: In scorecard - allow users to jump directly to the quiz - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/472
* 474: Allow setting up of admin password for accessing settings and course management - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/474
* 483: Add setting to allow removal of register option in app - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/483
* 488: Bug: viewing the course contents with the pre-test unpassed - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/488
* 489: Check all main activities extend AppActivity - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/489
* 471: Update activity task - give feedback if successful or not - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/471
* 495: Update Mint SDK jar file - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/495
* 496: Simplify querying for getting quizzes passed - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/496
* 481: Log out users after specified length of time - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/481
* 465: Add user prefs table - instead of using prefs activity - to help with shared devices - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/465
* 464: Can't start app with storage location set to external - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/464
* 497: Update the main scorecard (for multiple courses) so matches the individual course scorecard - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/497
* 482: How to enable more structured courses - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/482
* 512: Updated quiz jar file - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/512
* 498: Deal with deprecation of HTTP libraries - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/498
* 499: Pull in the Device Admin API option into the core code - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/499
* 517: DB errors: java.lang.IllegalStateException: attempt to re-open an already-closed object - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/517
* 424: Save searches into tracker - http://github.com/DigitalCampus/oppia-mobile-android/issues/issue/424

.. _appv55:

v55 (5.4.0) - released 24 Sept 2015
-------------------------------------

* 469: Check new scorecard calculating correctly - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/469



v54 (5.3.0) - released 15 Sept 2015
----------------------------------------------------

* 342: Change to using inline download bars when downloading courses/media - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/342
* 309: Run download media in background - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/309
* 177: Ability to select multiple media files for downloading - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/177
* 444: Stop activity timer when user switches to another app - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/444
* 445: Quiz feedback - app can crash on screen rotation - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/445
* 462: record in user table being recorded even when user is null - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/462
* 458: Store extra login info to help with shared device usage - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/458
* 307: Allow users to log back in without connection - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/307
* 423: Not-started course from SearchActivity - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/423
* 323: Make sure trackers and quizzes submitted for all users each time the service runs - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/323
* 451: Option to just download course activity file - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/451
* 454: QuizWidget saving the same tracker multiple times - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/454
* 456: Add quiz scorecard - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/456
* 457: Quiz results - store extra info to make it easier to calc results/scorecard - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/457

.. note::
	For some of the functionality now available in v54, the app must connect to an OppiaServer running at least :ref:`v0.8.0 <serverv0.8.0>`

v53 (5.2.0) - released 12 June 2015
--------------------------------------------------

* 427: App crashing when changing server setting - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/427
* 433: Add Urdu lang file from Bright Future app - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/433
* 435: Update Bugsense to Mint jar - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/435
* 437: Why are quiz results showing as 0% even when user has scored more - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/437
* 431: Activity tabs with long titles aren't shortening - so sometimes are unreadable - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/431
* 436: On the course homepage, the activity titles are being shortened to only one line - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/436
* 419: Remove dependency on ActionBarSherlock - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/419
* 440: Replace the default activity icons with blank background - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/440
* 449: Fail more cleanly when course files have been deleted from the sd card - https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/449

v52 (5.1.1) - released: 18 Mar 2015
---------------------------------------------------

* temporary fix for sd card issues

v51 (5.1.0) - released: 3 Mar 2015
---------------------------------------------------
* Now supports only v4 and above
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/391 - 
  allow password reset using email
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/383 - 
  quizzes getting recorded twice in tracker
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/393 - 
  implement URl activity
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/370 - 
  Enable rotating of the course and media download activities
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/375 - 
  Check there is sufficient space on device storage for downloading/moving files
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/376 - 
  Give option in preferences to move the storage location
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/334 - 
  Fix action bar theme colours
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/203 - 
  Allow screen rotation for tag select
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/349 - 
  Reloading quiz/feedback after language change 
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/409 - 
  Updated scorecard
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/376 - 
  preferences for storage option
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/349 - 
  Reloading quiz/feedback after language change  
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/368 - 
  embed videos into quiz and feedback activities
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/349 - 
  Reloading quiz/feedback after language change 
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/366 - 
  load images into gallery
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/349 - 
  Reloading quiz/feedback after language change 
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/229 - 
  deprecated method for preferences  
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/414 - 
  speed up searching
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/398 - 
  clicking on points/badges

v50 (5.0.1) - released: 30 Dec 2014
---------------------------------------------------
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/372 - 
  static prefs
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/379 - 
  setting to disable logout menu option
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/380 - 
  setting to disable course delete
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/377 - 
  setting to allow media download via cellular network
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/367 - 
  collapse keyboard between quiz questions
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/378 - 
  Apply ViewHolder pattern in ArrayAdapters
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/388 - 
  Require phone no on registration
* https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/390 - 
  highlighting wrong categories on tag select

v49 (5.0.0) - released beta version: 18 Nov 2014
---------------------------------------------------
* Fix https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/355 - 
  preventing media being visible to other apps
* Fix https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/371 - 
  use custom media player
* Fix https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/352 - 
  more reliable recording of media activity
* Fix https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/337 - 
  move file storage to new location

v48 (4.1.2) - released: 1 Oct 2014
--------------------------------------

* Fix https://github.com/DigitalCampus/oppia-mobile-android/issues/issue/364 - 
  prevent error when directory in downloads dir
* Fix https://github.com/DigitalCampus/mquiz-jar/issues/issue/5 - prevent error 
  when response title is an int rather than string