#!/usr/bin/env node
// Add or replace one blog post in blog-data.js.
// Usage: node tools/blog_add.js post.json
// post.json: {"date":"YYYY-MM-DD","title":"...","teaching":"...",
//             "tr":{"hi":{"title":"...","teaching":"..."}, "or":{...}, ...}}
// Languages: hi, or, bn, te, ta, gu, mr, kn, ml (any missing ones show in English).
const fs = require("fs"), path = require("path");
const file = path.join(__dirname, "..", "blog-data.js");
const post = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
if (!/^\d{4}-\d{2}-\d{2}$/.test(post.date) || !post.title || !post.teaching) throw new Error("date, title and teaching are required");
const LANGS = ["hi","or","bn","te","ta","gu","mr","kn","ml"];
const tr = {};
for (const c of LANGS) { const t = post.tr && post.tr[c]; if (t && t.title && t.teaching) tr[c] = { title: t.title, teaching: t.teaching }; }
global.window = {}; eval(fs.readFileSync(file, "utf8"));
const posts = (window.PK_BLOG && window.PK_BLOG.posts || []).filter(p => p.date !== post.date);
posts.push({ date: post.date, title: post.title, teaching: post.teaching, tr });
posts.sort((a, b) => (a.date < b.date ? 1 : -1));
const out = "/* Daily teaching points for Pandit Krishna Astrology.\n   One entry per date (YYYY-MM-DD, IST), newest first. Add posts with tools/blog_add.js.\n   tr holds the translations shown when a visitor picks another language. */\nwindow.PK_BLOG={posts:[\n" +
  posts.map(p => JSON.stringify(p)).join(",\n") + "\n]};\n";
fs.writeFileSync(file, out);
console.log("blog-data.js:", posts.length, "posts; " + post.date + " has", Object.keys(tr).length, "translations");
