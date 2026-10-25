# CampusLoop — Campus Gig & SkillSwap Portal

A student-friendly campus marketplace built for the MUET HacktoberFest issue.

## Technology

- HTML, CSS, JavaScript
- Vite for local development
- JSON Server for a REST-style mock API
- Seed data: 12 users, 25 gigs, 27 applications, 8 reviews

## Requirements

Install Node.js LTS (Windows x64): https://nodejs.org/en/download

## Run the project in VS Code

1. Extract the ZIP to a folder, for example `E:\University\Hackathon\campus-gig-skillswap`.
2. Open that folder in VS Code (`File → Open Folder`).
3. Open a terminal (`Terminal → New Terminal`).
4. Install the dependencies once:

   ```bash
   npm install
   ```

5. Start the mock API in terminal 1:

   ```bash
   npm run api
   ```

   Keep this terminal open. The API is at http://localhost:3000.

6. Click the `+` in the terminal panel to open **a second terminal**.
7. Start the website:

   ```bash
   npm run dev
   ```

8. Open the local URL Vite prints, usually http://localhost:5173.

## Features included

- Discover gigs, keyword search, category/type/payment/status filters, and a minimum/maximum budget range
- Create Offering and Requesting gigs
- Paid, SkillSwap, and Free payment options
- Profile editing and skill tags
- Apply with a message; duplicate and own-gig applications are blocked in the UI
- Owner-only applicant acceptance/rejection; accepting one applicant rejects other pending applications and moves the gig to In Progress
- Complete in-progress gigs
- Mutual review UI and stored average ratings, with a visible review action for eligible participants after completion
- Seed data in `db.json` (12 users, 25 gigs, 27 applications, 8 mutually consistent reviews; includes Open, In Progress, Completed, Expired, and Cancelled statuses)
- Warm rose-pink and cream visual theme with responsive laptop/mobile layout
- Demo account switcher in the top bar to test different student roles and the mutual review workflow

## Important demo notes

- Use the **Demo as** selector in the top bar to switch between seeded student accounts. This makes it easier to demonstrate posting, applying, owner actions, and both sides of the review flow. Profile editing updates the selected demo user.
- This is a hackathon mockup, not a production-secure service. JSON Server does not enforce real authentication/authorization; role rules are checked in frontend code for demonstration. A production deployment needs a real backend with server-side validation and authentication.
- Completed seed examples are gigs `4`, `10`, `15`, and `21`; each has a valid accepted applicant and a mutual review pair already stored. For a live review-form demo, select the owner of an In Progress gig, mark it Completed, switch to the accepted applicant, then submit one review from each participant. The review action only appears for eligible participants and only once per reviewer per gig.
- To reset all demo data, stop JSON Server and restore `db.json` from the original ZIP, or re-extract a fresh copy.

## API routes

JSON Server automatically provides:
- `GET /users`, `PATCH /users/:id`
- `GET /gigs`, `POST /gigs`, `PATCH /gigs/:id`
- `GET /applications`, `POST /applications`, `PATCH /applications/:id`
- `GET /reviews`, `POST /reviews`

Filtering examples:
- `GET /gigs?category=Design`
- `GET /gigs?type=Offering`
- `GET /gigs?q=portfolio` (JSON Server's query behavior depends on the field; frontend search is implemented client-side)

## Suggested 90-second demo

1. Show the Discover page and search/filter controls, including the budget range.
2. Open a gig and apply as the demo user to another student's open gig.
3. Show the Applications page.
4. Create a new gig and show it under My gigs.
5. Open an existing gig owned by user 1 (create one first if needed), accept a pending applicant, and show the status transition.
6. Show the profile and seeded review cards.
