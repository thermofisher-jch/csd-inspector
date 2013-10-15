<%inherit file="base.mako"/>

<h2 style="float: right">
    <a href="${request.static_url('lemontest:static/files/example_lemon_tests.zip')}">Download Example Tests</a>
</h2>
<h1>
    Ion Inspector Developer API
</h1>
<p>
    Ion Inspector is a Customer Support Archive testing automation server. When a
    CSA is uploaded to the server, a battery of tests are automatically run on
    the contents of the archive. Each of these tests reports the result of either
    a falsifiable hypothesis, i.e. OK/Alert/Warning, or performs some additional
    analysis from which no concrete determination can be made and human
    interpretation is required, i.e. Info. Any test reports a simple summary of
    its result status (OK/Alert/Warning/Info) along with more detailed, actionable
    information about the implications of the result, such as ("There are X% Q20
    reads, which is abnormally low."). This will be rendered in a table with the
    results of the other tests, e.g.
</p>
<table class="zebra-striped" id="test-summary">
    <thead>
        <tr>
            <th>Test</th><th>Status</th><th>Details</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Q20 Read Count</td>
            <td>
                <span class="label Alert">Alert</span>
            </td>
            <td>
                <p class="details">There are 7% Q20 reads, which is abnormally low.</p>
            </td>
        </tr>
    </tbody>
</table>
<p>
    A test is an executable named "main" in a directory named for the test. The
    executable can be a script or compiled binary in any language. For example,
    for a test "Low Read Quality" written Python, you would have to make a
    directory named <code>Low Read Quality</code> and put <code>main.py</code> in it (underscores may
    be substituted for spaces).
</p>
<p>
    <code>Q20 Read Count/main.py</code> or
    <code>Q20_Read_Count/main.py</code>
</p>
<p>
    <br />
</p>
<p>
    <strong>Optionally: </strong>if you
    include a <code>README</code> file in the Test Directory, its contents will be linked
    from the result table as a general description of what your test is/does and
    anything else a support specialist should know about your test. Either HTML
    or plain text will be rendered appropriately.
</p>
<p>
    <br />
</p>
<p>
    The Test Directory may contain any other information, modules, or ancillary
    files you would like.
</p>
<p>
    <strong>Requirements:</strong> the test itself, i.e. main.py, must meet the
    following requirements:
</p>
<ol>
    <li>
        <p>
            It must accept two directory paths as arguments, first the unpacked
            archive's directory and second the tests output folder. The Test
            Directory will be the current working directory.
            <code>main ARCHIVE OUTPUT</code>
        </p>
    </li>
    <li>
        <p>
            The test may not modify the files in <code>ARCHIVE</code> in anyway, read only.
        </p>
    </li>
    <li>
        <p>
            The test may write/copy/edit any files you want in <code>OUTPUT</code>, temporary
            and permanent results, but only to <code>OUTPUT</code>; no other directories may
            be written to including the Test Directory.
        </p>
    </li>
    <li>
        <p>
            Do not write to <code>OUTPUT/standard_output.log</code> or
            <code>OUTPUT/standard_error.log</code> These will be written automatically at the
            test's completion, containing it's stdout and stderr for logging
            convenience. Stderr will be written only if it is not empty.
        </p>
    </li>
    <li>
        <p>
            Your primary result information is returned through stdout in a
            specific format:
        </p>
        <table class="prettyprint">
            <tr>
                <td class="linenum">Line 1.</td>
                <td><em>final test result status</em> (OK/Alert/Warning/Info, etc.)</td>
            </tr>
            <tr>
              <td class="linenum">Line 2.</td>
                <td><em>integer result priority</em> (This is 0 to
              100 and is used for sorting the test results by
              importance, descending order)</td>
            </tr>
            <tr>
              <td class="linenum">Lines 3+</td>
                <td><em>test result details</em> (A concrete,
              explanation of the specific results of this test run)</td>
            </tr>
        </table>
        <p>
            All output on and after the
            3<sup>rd</sup> line
             will be written to the details column in the test result
            table. Use this for a medium length, test run specific explanation of
            the result. Everything written to <code>OUTPUT</code> will be accessible, so any
            other result data can be read.
        </p>
    </li>
</ol>
<p>
    Use these output statuses and priority numbers for lines 1 and 2 in the output above.
    <table class="table">
        <thead>
            <tr>
                <th>Status</th>
                <th>Priority</th>
                <th>When?</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Alert</td>
                <td>40</td>
                <td>Conclusively or highly likely to be a problem.</td>
            </tr>
            <tr>
                <td>Warning</td>
                <td>30</td>
                <td>Potentially a problem neither, conclusively failed nor likely acceptable.</td>
            </tr>
            <tr>
                <td>Info</td>
                <td>20</td>
                <td>No positive or negative analysis at all, e.g. graphs.  Don't use this if at all avoidable.</td>
            </tr>
            <tr>
                <td>OK</td>
                <td>10</td>
                <td>Likely acceptable, conditions which are probably not the problem, while not necessarily 100% guaranteed to be safe.</td>
            </tr>
            <tr>
                <td>N/A</td>
                <td>0</td>
                <td>The test cannot run on the archive at all.  This is a graceful failure mode.</td>
            </tr>
        </tbody>
    </table>
</p>
<p>
    <strong>Optionally</strong>, if you have very rich or lengthly result
    information, the test may write a <code>OUTPUT/results.html</code> file. This file
    will automatically be detected, if it is created, and linked to from the test
    result table. Feel free to make <code>results.html</code> as complex as you like: you can
    write other html files, images, style sheets or JavaScript, all linking to
    one another, really, just go nuts.
</p>