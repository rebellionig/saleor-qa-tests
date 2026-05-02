import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '30s', target: 50 },
    { duration: '30s', target: 100 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<3000'],
    http_req_failed: ['rate<0.05'],
  },
};

const URL = 'http://localhost:8000/graphql/';

export default function () {
  const payload = JSON.stringify({
    query: `
      mutation {
        checkoutCreate(
          input: {
            channel: "default-channel"
            email: "test@example.com"
            lines: []
          }
        ) {
          checkout {
            id
            token
          }
          errors {
            field
            message
          }
        }
      }
    `,
  });

  const params = {
    headers: { 'Content-Type': 'application/json' },
  };

  const res = http.post(URL, payload, params);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'checkout created or errors returned': (r) => {
      const body = JSON.parse(r.body);
      return body.data !== undefined;
    },
  });

  sleep(1);
}