import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },  // normal load
    { duration: '30s', target: 50 },  // peak load
    { duration: '30s', target: 100 }, // stress load
    { duration: '30s', target: 0 },   // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.05'],
  },
};

const URL = 'http://localhost:8000/graphql/';

export default function () {
  const payload = JSON.stringify({
    query: `
      mutation {
        tokenCreate(email: "admin@example.com", password: "admin") {
          token
          errors { field message }
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
    'no errors': (r) => {
      const body = JSON.parse(r.body);
      return !body.errors;
    },
  });

  sleep(1);
}