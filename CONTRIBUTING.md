# Contribution Guidelines

## Getting Help

If you have any questions about anything in this document, please
feel free to [file an issue][], or add a comment to your 
[work-in-progress][wip-pr] pull request!

## Reporting Issues

- **Search for existing issues.** Please check to see if someone else
  has reported the same issue.
- **Share as much information as possible.** Include operating system
  and version, browser and version. Also, include steps to reproduce
  the bug.
- If you're experiencing a visual bug, consider [attaching][] a
  [screenshot][] to your issue. It's extremely helpful.

## Contributing Code Changes

This project embraces the concept of [Work-In-Progress Pull Requests][wip-pr]:

> In our team, we send Pull Requests as soon as there’s one commit in a new 
> branch. Or even empty commit.
>
> `git commit -m "initial commit: User can verify their account" --allow-empty`
>
> Contributor starts with some basic ideas, small patches, failing tests.
> And then the PR grows collaboratively. Somebody contributes with comment. 
> Somebody does commit. Sometimes commits are reverted and replaced with
> better solutions. It’s like an asynchronous pair programming with
> unlimited collaborators. The value is tremendous.

So, you're encouraged to create your PR as early as possible; just start
its name with `[WIP]` to indicate that it's a work-in-progress. You can
even include a [Markdown Task List][] to indicate what still needs to be
done, if you want.

When your PR is ready for a final merge, remove the `[WIP]` from the
beginning of its name and leave a comment. That's it!

Some other things to keep in mind:

- Before marking a PR for final review, run `python manage.py test` to
  ensure that everything still works.
- Try to share which browsers and devices your code has been tested on.
- If your PR resolves an issue, include **fixes #ISSUE_NUMBER** in your
  commit message (or a [synonym][]). It's okay if you forget to do this,
  though, as it's just a convenience.
- If your PR contains a user interface change, consider [attaching][] a
  [screenshot][] to its description. It's helpful!

## Code Style

For most files, try to limit your line length to a maximum of 80
characters. The major exception to this is HTML files and templates,
where anything goes.

### Python

- [PEP 8][] all the way!

### HTML

- 2 space indentation
- Class names use hypenated case (e.g. `my-class-name`)

### SASS / CSS

- 2 space indentation
- Always a space after a property's colon (e.g. `display: block;`
  *not* `display:block;`)
- End all lines with a semicolon

## Testing

### Automated Testing

If you're writing any Python code, please add automated tests 
to exercise it. Guidance on how to do this can be found in the
[README][]. If you need any help, please ask!

Unfortunately, the project does not yet have a browser-side
JavaScript test suite; work on this is being tracked in [#37][].

### Manual Testing

#### Browsers

If possible, manually test your changes on the latest version of
Firefox, Chrome, Internet Explorer, and Safari.

To ensure that the site is accessible, consider using a
screen reader like [VoiceOver][] (OS X) or [NVDA][] (Windows) to
visit any pages you've added or changed. And if you've added
or changed any JavaScript-based logic for UI, make sure it
satisfies the Paciello Group's [Web Components punch list][].

##### HTML5 Form Validation

If you've created or made changes to any forms, make sure they
work with browsers that don't support HTML5 form validation
by using the [novalidate][] bookmarklet. Alternatively, you can
paste the following into your Web console before submitting a form:

```javascript
for(var f=document.forms,i=f.length;i--;)f[i].setAttribute("novalidate",i)
```

##### Diagnostics

For any pages you've added or changed, make sure you
use [PageSpeed Insights][], [WebPagetest][], and/or
[What Does My Site Cost][] to ensure the page performs
acceptably across a range of devices and bandwidths. Use
[Tenon][] and [Color Oracle][] to ensure it's accessible.

You can use a tunneling program like [ngrok][] to make your local
development setup visible to these kinds of tools.

##### HTTPS

We often develop using http, but the production site is always
hosted via https. Consider using a tool like [ngrok][] to easily
tunnel into your local server over https to ensure that your
changes haven't introduced any [Mixed Content][] warnings.


[PEP 8]: https://www.python.org/dev/peps/pep-0008/
[#37]: https://github.com/GovLab/noi2/issues/37
[file an issue]: https://github.com/GovLab/noi2/issues/new
[wip-pr]: http://vrybas.github.io/blog/2014/04/11/wip-pull-requests/
[Markdown Task List]: https://github.com/blog/1375-task-lists-in-gfm-issues-pulls-comments
[attaching]: https://github.com/blog/1347-issue-attachments
[screenshot]: https://www.google.com/search?q=how+to+take+a+screenshot
[README]: https://github.com/GovLab/noi2#readme
[synonym]: https://help.github.com/articles/closing-issues-via-commit-messages
[PageSpeed Insights]: https://developers.google.com/speed/pagespeed/insights/
[WebPagetest]: http://www.webpagetest.org/
[What Does My Site Cost]: http://whatdoesmysitecost.com/
[Tenon]: http://tenon.io/
[Color Oracle]: http://colororacle.org/
[ngrok]: https://ngrok.com/
[Mixed Content]: https://developer.mozilla.org/en-US/docs/Security/MixedContent
[VoiceOver]: http://webaim.org/articles/voiceover/
[NVDA]: https://www.marcozehe.de/articles/how-to-use-nvda-and-firefox-to-test-your-web-pages-for-accessibility/
[Web Components punch list]: http://www.paciellogroup.com/blog/2014/09/web-components-punch-list/
[novalidate]: http://novalidate.com/
