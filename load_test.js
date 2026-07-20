import http from 'k6/http';
import { check, sleep } from 'k6';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';
import encoding from 'k6/encoding';

export const options = {
    setupTimeout: '5m',
    scenarios: {
        ramp_up_load: {
            executor: 'ramping-vus',
            startVUs: 100,
            stages: [
                { duration: '30s', target: 50 },
                { duration: '1m', target: 150 },
                { duration: '30s', target: 150 },
                { duration: '30s', target: 0 },
            ],
            gracefulRampDown: '10s',
        },
    },
    thresholds: {
        http_req_duration: ['p(50)<200', 'p(95)<500', 'p(99)<1000'],
        http_req_failed: ['rate==0'],
    },
};

const TEST_USERS = [
    { email: 'email', password: 'password' },
    // in this format
    
];

function decodeUserId(token) {
    const payload = token.split('.')[1];
    const decoded = JSON.parse(encoding.b64decode(payload, 'rawstd', 's'));
    return parseInt(decoded.sub);
}

export function setup() {
    const sessions = [];
    for (const u of TEST_USERS) {
        const res = http.post('http://127.0.0.1:8000/auth/login', JSON.stringify({
            email: u.email,
            password: u.password,
        }), { headers: { 'Content-Type': 'application/json' } });

        if (res.status !== 200) {
            console.log(`Login FAILED for ${u.email}: status ${res.status}`);
            continue; // skip this user instead of crashing
        }

        const token = res.json('access_token');
        const userId = decodeUserId(token);
        sessions.push({ token, userId });
    }
    return { sessions };
}

export default function (data) {
    const sessions = data.sessions;
    const senderIdx = Math.floor(Math.random() * sessions.length);
    let receiverIdx = Math.floor(Math.random() * sessions.length);
    while (receiverIdx === senderIdx) {
        receiverIdx = Math.floor(Math.random() * sessions.length);
    }
    const sender = sessions[senderIdx];
    const receiver = sessions[receiverIdx];

    const url = 'http://127.0.0.1:8000/transactions/transfer';
    const payload = JSON.stringify({
        receiver_user_id: receiver.userId,
        amount: 1.0,
    });
    const params = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${sender.token}`,
            'Idempotency-Key': uuidv4(),
        },
    };

    const res = http.post(url, payload, params);
    check(res, {
        'is status 200': (r) => r.status === 200,
        'transaction successful': (r) => r.json('status') === 'SUCCESS',
        'no conflict': (r) => r.status !== 409,
        'no server error': (r) => r.status !== 500,
    });
    sleep(1);
}