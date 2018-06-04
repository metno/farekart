import json
import os

class event_awareness_parameters:
    def __init__(self,event_type, lang,certainty,severity):
        eventSeverityParameters=self.read_json()
        self.event_types = eventSeverityParameters['eventTypes']
        if event_type not in self.event_types:
            print("Warning: %s is not a supported event type!" % event_type)
        self.events = eventSeverityParameters['eventNames'][event_type][lang]
        # should depend on severity and certainty
        awareness =  eventSeverityParameters['awareness'][certainty][severity]
        try:
            self.eventAwarenessName = \
            eventSeverityParameters['eventAwarenessName'][event_type][certainty][lang][severity]
        except:
            self.eventAwarenessName=""
        self.awarenessResponse = eventSeverityParameters['awarenessResponse'][lang][awareness]

        self.awarenessSeriousness = eventSeverityParameters['awarenessSeriousness'][lang][awareness]

        # MeteoAlarm mandatory elements
        self.awareness_types = eventSeverityParameters['awareness_types'].get(event_type, "")
        self.awareness_levels = eventSeverityParameters['awareness_levels'].get(awareness, "")




    def read_json(self):
        filename ="eventSeverityParameters.json"
        filename_local= os.path.join("etc",filename)
        filename_global = os.path.join(os.sep, "etc", "farekart", filename)
        if (os.path.isfile(filename_local)):
            filename=filename_local
        else:
            filename=filename_global
        with open(filename, "r") as file:
            esp= file.read()

        eventSeverityParameters=json.loads(esp)
        return eventSeverityParameters




