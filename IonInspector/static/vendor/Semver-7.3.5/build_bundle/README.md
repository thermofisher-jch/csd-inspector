This file is not an as-is distribution file produced by semver's authors.  It had to be derived by the following procedure,
documented here for the sake of maintainability over time, and because Inspector currently has no compile time build process
to drive this workflow from.  It could be performed inside of a Dockerfile in theory, but Docker here should be used for
enacapsulating a build that was already completed outside of the Dockerization process.  To perform this derviation inside that
packaging would invert the order of dependency and make "building" Inspector depend upon packaging it with Docker, instead of
the other way around.

1)  Create a workspace directory and make sure a current revision of node is on your PATH.
```
	mkdir worksapce;
	cd workspace
```

2)  Acquire semver and the `browserify` development tool we'll use to preprocess it for consumption from the browser.
```
	npm install --save semver
	npm install --save-dev browserify
```

3) Create a NodeJS script that loads semver's main module and binds it to a constant name.  This constant will become a global
   in the browser's namespace bound to the Semver library when we are done.
```
	echo "const semver = require(\"semver\");\n" > require_semver.js
```

4) Run browserify to derive a Javascript file that will achieve the global binding described in (3) above:
```
	./node_modules/.bin/browserify require_semver.js > browser_semver.js
```

5) Move the resulting file back up to the parent directory and commit it to the repository.  This is what you will add to a <script>
   tag in any HTML Template where we want to use the `semver` library.
```
	mv browser_semver.js ../semver.js
	git add ../semver.js
	git commit -m 'Updated browserified encapsulation of Semver v7.3.5'
```

