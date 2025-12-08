@ECHO OFF
REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
set BUILDDIR=_build
set ALLSPHINXOPTS=-d %BUILDDIR%/doctrees %SPHINXOPTS%

if NOT "%PAPER%" == "" (
	set ALLSPHINXOPTS=%ALLSPHINXOPTS% -D latex_paper_size=%PAPER%
)

if "%1" == "" goto targets

if "%1" == "clean" (
	for /d %%i in (%BUILDDIR%\*) do (rmdir /q /s %%i)
	del /q /s %BUILDDIR%\*.*
	goto end
)

if "%1" == "html" (
	%SPHINXBUILD% -b html %ALLSPHINXOPTS% . %BUILDDIR%\html
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The HTML documentation is in %BUILDDIR%\html.
	goto end
)

if "%1" == "help" (
	%SPHINXBUILD% -M help . %BUILDDIR%
	goto end
)

REM Default: route to sphinx-build
%SPHINXBUILD% -M %1 %ALLSPHINXOPTS% . %BUILDDIR%

:targets
echo.Please use `make ^<target^>` where ^<target^> is one of
echo.  html       to make standalone HTML files
echo.  clean      to make a clean build
echo.
goto end

:end
