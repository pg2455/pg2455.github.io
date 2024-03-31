[![Build Status](https://travis-ci.com/pg2455/pg2455.github.io.svg?branch=master)](https://travis-ci.com/pg2455/pg2455.github.io)

# About
This is the source code for my personal website.
Unless stated otherwise, all content is MIT-licensed.

# w3c compliance continuous integration
Travis CI builds the static website with Jekyll and uses
[validate.rb](validate.rb) to check content for w3c compliance.
Simon Sigurdhsson wrote the
[original validate.rb script](https://github.com/urdh/blog/blob/gh-pages/validate.rb),
available in the public domain by the CC0 license,
and the modifications here are also available in the public domain
by the CC0 license.

# Installation

You will need Ruby 2.7.0, as this is the version used by GitHub Pages. For detailed instructions on managing different versions of Ruby and switching between them, visit the [Jekyll installation page](https://jekyllrb.com/docs/installation/macos/). Make sure to have the following in your shell so that it has access to the right compilers (for MacOS - it needs access to libffi).

```zsh
export LDFLAGS="-L/opt/homebrew/opt/libffi/lib"
export CPPFLAGS="-I/opt/homebrew/opt/libffi/include"
export PKG_CONFIG_PATH="/opt/homebrew/opt/libffi/lib/pkgconfig"
```

Once installed, you can use `bundle install` to install the dependencies and `bundle exec jekyll serve` to serve the website.

**NOTE**: This is a fork of [Brandon Amos's Personal Website](http://github.com/bamos/bamos.github.io/) adapted for my needs.
