/// <reference types="@google/local-home-sdk" />
const axios = require('axios').default;
const apiClient = axios.create({
  baseURL: 'http://192.168.1.173:8081',
  responseType: 'json',
  headers: {
    'Content-Type': 'application/json'
  }
});

const app = new smarthome.App("1.0.0")
  .onIdentify((request) => {
    console.debug("IDENTIFY request:", request);

    const device = request.inputs[0].payload.device;

    return new Promise((resolve, reject) => {
      const response = {
        intent: smarthome.Intents.IDENTIFY,
        requestId: request.requestId,
        payload: {
          device: {
            id: 'ps4' || "",
          },
        },
      };
      console.log("IDENTIFY response", response);
      resolve(response);
    });
  })
  .onExecute((request) => {
    console.debug("EXECUTE request", request);

    const response = new smarthome.Execute.Response.Builder()
      .setRequestId(request.requestId);
    const command = request.inputs[0].payload.commands[0];
    const execution = command.execution[0];
    const params = execution.params;
    console.log("command", command);
        
    const result =  command.devices.map((device) => {
      const states = {
        status: 'SUCCESS',
        state:{on: true,
          online: true,}
        
      };
      const params = new URLSearchParams();
      return apiClient.post('/action', execution)
        .then(function (hresponse : any) {
          // handle success
          console.log(hresponse);
          response.setSuccessState(device.id, states);
        })
        .catch(function (error : any) {
          // handle error
          console.log(error);
          response.setErrorState(device.id, "ERROR");
        })
        .finally(function () {
          // always executed
        });
    });
    
    return Promise.all(result).then(() => {
      return response.build()
    });
  })
  .listen()
  .then(() => {
    console.log("Ready for PS4");
  });
