--- Database commands to insert the new plugin into FogLAMP

--- Create the south service instannce
INSERT INTO foglamp.scheduled_processes ( name, script ) VALUES ( 'AM2315',   '["services/south"]' );

--- Add the schedule to start the service at system startup
INSERT INTO foglamp.schedules ( id, schedule_name, process_name, schedule_type,
                                schedule_time, schedule_interval, exclusive, enabled )
       VALUES ( '56450027-824e-417b-a5d3-0f9a4211aaa5', -- id
                'AM2315 async south',                 -- schedule_name
                'AM2315',                             -- process_name
                1,                                      -- schedule_type (startup)
                NULL,                                   -- schedule_time
                '00:00:00',                             -- schedule_interval
                true,                                   -- exclusive
                true                                    -- enabled
              );

--- Insert the config needed to load the plugin
INSERT INTO foglamp.configuration ( key, description, value )
    VALUES ( 'AM2315',
             'AM2315 async South Plugin',
             ' { "plugin" : { "type" : "string", "value" : "am2315async", "default" : "am2315async", "description" : "Python module name of the plugin to load" } } '
           );

