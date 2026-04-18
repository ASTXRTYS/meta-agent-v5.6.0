# Meta Harness Web App Pass

Self-contained React/Vite frontend pass for the Meta Harness landing, sign-in, and Project Manager cockpit blank slate.

## Run

```bash
npm install
npm run dev
```

The current local dev URL is `http://127.0.0.1:5173/`.

## Verify

```bash
npm run lint
npm run build
```

## Product Notes

- Landing page follows the Stripe-family hypothesis: light-primary, calm, and operator-trustworthy.
- Sign-in is local mock auth only; the auth provider decision is still open in the product docs.
- New PM threads create local project objects in the prototype. Backend integration should later replace this local state with `useStream`.
- The right project rail starts empty, then surfaces filesystem artifacts, eval datasets, and LangSmith handoff links once a project exists.
