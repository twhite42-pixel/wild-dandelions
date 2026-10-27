# Wild Dandelions

The website for Wild Dandelions, by Torie White.

---

## Start the website

Double-click **`Start the website.command`** in Finder.

A black window opens and stays open — that is the website running. Leave it
there. Then open your browser to:

> **http://localhost:5050**

To stop the site, close that black window (or press `Control` + `C` in it).

Prefer the terminal? From this folder:

```
./.venv/bin/python app.py
```

> The site runs on port **5050**, not the usual 5000, because macOS gives
> port 5000 to AirPlay and it silently blocks the page.

---

## Make the contact form actually send you email

Until you do this, the form shows a polite message telling people to email
you directly. It never breaks — it just can't send yet.

Google won't let a program use your normal password, so you create a separate
16-character "app password" just for this website. Takes about two minutes.

1. Go to **https://myaccount.google.com/security**
2. Turn on **2-Step Verification** if it isn't already. App passwords don't
   exist without it.
3. Go to **https://myaccount.google.com/apppasswords**
4. Type a name — `Wild Dandelions website` — and click **Create**.
5. Google shows you 16 letters in a yellow box, like `abcd efgh ijkl mnop`.
   Copy them.
6. In this folder, make a copy of `.env.example` and name it `.env`
7. Open `.env` and paste the 16 letters after `GMAIL_APP_PASSWORD=`,
   with the spaces taken out:

   ```
   GMAIL_ADDRESS=toriewhite9@gmail.com
   GMAIL_APP_PASSWORD=abcdefghijklmnop
   ```

8. Stop the website and start it again.

Now the form sends to **toriewhite9@gmail.com**. Replies go straight back to
whoever wrote in, so you can just hit Reply.

**Keep `.env` private.** Anyone with that password can send email as you. It
is already excluded from git, so it won't get shared by accident. If you ever
think it leaked, delete it at the apppasswords link above and make a new one.

---

## Change your products

Open **`products.json`**. Everything in the shop lives there. Edit it, save,
refresh the browser — no restart needed.

Each piece looks like this:

```json
{
  "id": "sunset-marble",
  "name": "Sunset Marble",
  "price": "$24",
  "blurb": "Hand-marbled clay, swirled red and sky blue.",
  "image": "sunset-marble.jpg",
  "etsy_url": "",
  "sold_out": false
}
```

| What | What to do |
|---|---|
| **Change a price** | `"price"` is just text. `"$24"`, `"$20 - $30"` and `"Made to order"` all work. |
| **Link to Etsy or Shopify** | Paste the listing link into `"etsy_url"`. The button changes from "Email me about these" to "Buy on Etsy" on its own. |
| **Mark something sold** | Change `"sold_out"` to `true`. It gets a Sold Out tag and the button becomes "Ask for another pair". |
| **Hide a piece** | Delete its block, including the `{` and `}` and the comma. |
| **Add a new piece** | Put the photo in `public/static/img/products/`, then copy an existing block and change the details. `"image"` must match the filename exactly. |

> Product photos look best upright, roughly 3-wide by 4-tall, on a plain
> white background — the same way you shot the current ones.

### One catch about the handwriting font

Your handwriting font only contains letters and `' " , . : ; ? !` — it has
**no numbers, no hyphens, and no `&`**. That's why prices are set in the
serif font instead.

If you name a piece `Flower #2`, the `#2` quietly falls back to the serif and
looks out of place. Stick to letters and spaces in product names.

---

## Change your story, or the photo beside it

Both are in `templates/index.html`, under the line that says
`<!-- TORIE: rewrite the two paragraphs below in your own words. -->`

The two paragraphs there are a draft in your voice — please replace them with
your own words.

The framed photo next to it is currently a pair of earrings. If you'd rather
have a photo of **you**, drop it into `public/static/img/`, then change
`img/products/cherry-blossom.jpg` on the line just below to your filename.

---

## What's in this folder

```
app.py                  The Python server. Serves the page, sends your email.
products.json           Your shop. The file you'll edit most.
.env                    Your Gmail app password. Private, never shared.
templates/index.html    The page itself.
public/static/css/style.css   All the styling.
static/js/main.js       The photo pop-up and the contact form.
static/img/             Your logo and product photos.
static/fonts/           Your handwriting.
tests/                  Automated checks for the contact form.
tools/                  One-off script that cut the hero earrings out of
                        their white backgrounds. You won't normally need it.
```

---

## Checking nothing is broken

```
./.venv/bin/python -m pytest tests/ -q
```

22 checks covering the contact form: that good messages send, that bad email
addresses are refused, that spam bots are ignored, and that you're told
clearly when Gmail isn't set up yet.

---

## The live website

The site is hosted free on **Vercel**, and its code lives on GitHub at
**https://github.com/twhite42-pixel/wild-dandelions**

### Publishing a change

Edit a file, then from this folder:

```
git add -A
git commit -m "Say what you changed"
git push
```

Vercel notices the push and puts the new version live in about a minute.
That's the whole process - no uploading, no dragging files anywhere.

This is how you'd change a price, add a piece, or rewrite your About
paragraphs once the site is public.

### Your Gmail password on the live site

The `.env` file never leaves your computer, so the live site needs to be told
the app password separately. Once, in Vercel:

1. Go to your project on **vercel.com**
2. **Settings** -> **Environment Variables**
3. Add `GMAIL_ADDRESS` = `toriewhite9@gmail.com`
4. Add `GMAIL_APP_PASSWORD` = your 16 letters
5. **Deployments** -> the top one -> **Redeploy**

Until you do, the live form tells people to email you directly instead.

### A custom domain

A name like `wilddandelions.com` costs around $12 a year from a registrar -
Vercel itself sells them, as do Namecheap and Cloudflare. Pointing it at the
site is free: **Settings** -> **Domains** -> type the name. Vercel walks you
through the rest.
