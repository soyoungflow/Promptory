/**
 * Promptory k6 스모크 부하 테스트
 *
 * 사용법 (EC2 또는 로컬 nginx :80 기준):
 *   k6 run -e BASE_URL=http://13.211.8.186 scripts/k6/smoke.js
 *
 * 결과 해석 가이드: docs/BONUS_POINTS_PLAN.md
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1';

const errorRate = new Rate('errors');
const homeDuration = new Trend('home_duration', true);
const promptsDuration = new Trend('prompts_list_duration', true);
const aiHealthDuration = new Trend('ai_health_duration', true);

export const options = {
  stages: [
    { duration: '30s', target: 5 },
    { duration: '1m', target: 10 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<2000'],
    errors: ['rate<0.05'],
  },
};

function get(path) {
  const res = http.get(`${BASE_URL}${path}`, { tags: { name: path } });
  const ok = check(res, {
    [`${path} status 200`]: (r) => r.status === 200,
  });
  errorRate.add(!ok);
  return res;
}

export default function () {
  const home = get('/');
  homeDuration.add(home.timings.duration);

  const prompts = get('/api/prompts/?page=1');
  promptsDuration.add(prompts.timings.duration);

  const ai = get('/ai/health');
  aiHealthDuration.add(ai.timings.duration);

  sleep(1);
}

export function handleSummary(data) {
  const p95 = data.metrics.http_req_duration?.values?.['p(95)'] ?? 0;
  const avg = data.metrics.http_req_duration?.values?.avg ?? 0;
  const failed = data.metrics.http_req_failed?.values?.rate ?? 0;
  return {
  stdout: [
    '',
    '=== Promptory k6 요약 ===',
    `BASE_URL: ${BASE_URL}`,
    `평균 응답: ${avg.toFixed(1)} ms`,
    `p95 응답: ${p95.toFixed(1)} ms`,
    `에러율: ${(failed * 100).toFixed(2)} %`,
    '발표용: Grafana HTTP 패널과 비교해 병목(nginx vs Django vs DB)을 설명하세요.',
    '',
  ].join('\n'),
  };
}
