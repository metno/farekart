import json
import os

class event_awareness_parameters:
    def __init__(self,event_type, lang,certainty,severity):
        eventSeverityParameters=self.read_json()
        self.event_types = eventSeverityParameters['eventTypes']
        self.events = eventSeverityParameters['eventNames'][event_type][lang]
        self.eventAwarenessName = \
            eventSeverityParameters['eventAwarenessName'][event_type][certainty][lang][severity]
        self.awarenessResponse = eventSeverityParameters['awarenessResponse'][lang][severity]
        self.awarenessSeriousness = eventSeverityParameters['awarenessSeriousness'][lang][severity]

        # MeteoAlarm mandatory elements
        self.awareness_types = eventSeverityParameters['awareness_types'].get(event_type, "")
        self.awareness_levels = eventSeverityParameters['awareness_levels'].get(severity, "")




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


    def getSeverityResponse(self,phenomenon_name):

        response = self.awarenessResponse
        if (phenomenon_name):
            response+=phenomenon_name
        return response



