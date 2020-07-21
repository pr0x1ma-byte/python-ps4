/**
 * Copyright 2020, Google LLC
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *   http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import 'ts-polyfill/lib/es2019-array';

import { smarthome } from 'actions-on-google';
import * as functions from 'firebase-functions';

const device = {
  'id': 'ps4',
  'name': 'Grant\s PS4',
  'port': 8080
};

const app = smarthome({ debug: true });

app.onSync((body, headers) => {
  return {
    requestId: body.requestId,
    payload: {
      agentUserId: 'placeholder-user-id',
      devices: [{
        type: 'action.devices.types.TV',
        traits: [
          'action.devices.traits.OnOff',
          'action.devices.traits.AppSelector',
        ],
        id: device.id,
        otherDeviceIds: [{
          deviceId: device.id,
        }],
        name: {
          name: device.name,
          defaultNames: [],
          nicknames: ['playstation'],
        },
        willReportState: true,
        customData: {
          port: device.port,
        },
        attributes: {
          availableApplications: [
            {
              key: 'amazon',
              names: [
                {
                  name_synonym: [
                    'amazon',
                  ],
                  'lang': 'en'
                },
              ]
            },
            {
              key: 'netflix',
              names: [
                {
                  name_synonym: [
                    'netflix',
                    'Netflix US'
                  ],
                  'lang': 'en'
                },
              ]
            },
             {
              key: 'disney',
              names: [
                {
                  name_synonym: [
                    'disney',
                    'disney plus',
                    'disney+'
                  ],
                  'lang': 'en'
                },
              ]
            }],

        },
      }],
    },
  };
});
app.onQuery((body, headers) => {
  return {
    requestId: body.requestId,
    payload: {
      devices: [],
    },
  };
});
exports.smarthome = functions.https.onRequest(app);

exports.authorize = functions.https.onRequest((req, res) => {
  const redirectUri = req.query.redirect_uri as string;
  res.status(200).send(`<a href="${
    decodeURIComponent(redirectUri)}?code=placeholder-auth-code&state=${
    req.query.state}">Complete Account Linking</a>`);
});

exports.token = functions.https.onRequest((req, res) => {
  res.status(200).send({
    token_type: 'bearer',
    access_token: 'placeholder-access-token',
    refresh_token: 'placeholder-refresh-token',
    expires_in: 3600,
  });
});
