# Overview

photo-feed is an Instagram-style photo feed with inline checkout.
A user posts a photo (optionally with a price), other users can buy
it. Around that loop, two AI-adjacent flows run on the side:

- **Cut a posted image** down to a feed-friendly variant
  automatically when it's uploaded.
- **Generate a new image** from a text prompt — the user can then
  post the generated picture like any other.

## What a user can do

- Register, log in, log out.
- Browse the feed, view a single post, see other users' profiles.
- Upload a photo, write a caption, optionally set a price.
- Add priced posts to a cart, check out, see order history.
- Submit a text prompt and get an AI-generated image back to post.

## Demo data

Every fresh clone gets seeded users, posts, and orders via
`make seed-all`. Demo accounts use `<handle>@photo-feed.local`
emails and password `pass1234`. `make reset` wipes every user
(CASCADE removes their posts and orders) so you can start over.
