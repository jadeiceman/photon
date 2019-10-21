%global perl_version 5.28.0
%global perl_cross_version 1.3

# Got the intial spec from Fedora and modified it
Summary:        SQLite DBI Driver
Name:           perl-DBD-SQLite
Version:        1.62
Release:        1%{?dist}
Group:          Development/Libraries
License:        (GPL+ or Artistic) and Public Domain
URL:            http://search.cpan.org/dist/DBD-SQLite/
Source0:        https://cpan.metacpan.org/authors/id/I/IS/ISHIGAKI/DBD-SQLite-%{version}.tar.gz
%define sha1    DBD-SQLite=e4fb2fca987e92f5949fb5a50990bc963f8fe164
%if "%{?cross_compile}" != ""
Source1:        http://www.cpan.org/src/5.0/perl-%{perl_version}.tar.gz
Source2:        https://github.com/arsv/perl-cross/releases/download/%{perl_cross_version}/perl-cross-%{perl_cross_version}.tar.gz
%endif
Vendor:         VMware, Inc.
Distribution:   Photon
BuildRequires:  sqlite-devel >= 3.22.0
BuildRequires:  perl >= 5.28.0
BuildRequires:  perl-DBI
Requires:       perl-DBI
Requires:       perl >= 5.28.0

%description
SQLite is a public domain RDBMS database engine that you can find at
http://www.hwaci.com/sw/sqlite/.

This module provides a SQLite RDBMS module that uses the system SQLite
libraries.

%prep
%setup -q -n DBD-SQLite-%{version}

%if "%{?cross_compile}" != ""
export CC="%{_host}-gcc"
export CXX="%{_host}-g++"
export AR="%{_host}-ar"
export AS="%{_host}-as"
export RANLIB="%{_host}-ranlib"
export LD="%{_host}-ld"
export STRIP="%{_host}-strip"

echo "Setting up perl cross-compile..."
%setup -q -b 2 -n perl-cross-%{perl_cross_version}
%setup -q -b 1 -n perl-%{perl_version}
cp -r %{_builddir}/perl-cross-%{perl_cross_version}/* . -v
cp -r %{_builddir}/DBD-SQLite-%{version} cpan/ -v

%endif

%build
%if "%{?cross_compile}" != ""
CONFIGURE_OPTS="\
    --prefix=%{_prefix} \
    --target=%{_host} \
    -Dvendorprefix=%{_prefix} \
    -Dman1dir=%{_mandir}/man1 \
    -Dman3dir=%{_mandir}/man3 \
    -Duseshrplib \
    -Dusethreads \
    -DPERL_RANDOM_DEVICE=/dev/erandom \
    --only-mod= \
"
./configure $CONFIGURE_OPTS

make %{?_smp_mflags}

sed -i 's:exec $top/miniperl:exec perl:g' miniperl_top

%ifarch arm
%global perl_vendorarch %(%{_builddir}/perl-%{perl_version}/miniperl_top -V:vendorarch | cut -d "'" -f 2)
%endif

cd cpan/DBD-SQLite-%{version}

../../miniperl_top Makefile.PL PERL_CORE=1 PERL=../../miniperl_top INSTALLDIRS=vendor

%else
CFLAGS="%{optflags}" perl Makefile.PL INSTALLDIRS=vendor
%endif

make %{?_smp_mflags} OPTIMIZE="%{optflags}"

%install
%if "%{?cross_compile}" != ""
# Install spits out extra files because of the cross compile, so ignore them
%define _unpackaged_files_terminate_build 0
cd cpan/DBD-SQLite-%{version}
%endif

make pure_install DESTDIR=%{buildroot}
find %{buildroot} -type f \( -name .packlist -o \
     -name '*.bs' -size 0 \) -exec rm -f {} ';'
%{_fixperms} %{buildroot}/*

%check
make test

%files
%{perl_vendorarch}/auto/*
%{perl_vendorarch}/DBD/
%{_mandir}/man3/*

%changelog
*   Tue Jan 22 2019 Michelle Wang <michellew@vmware.com> 1.62-1
-   Update to version 1.62.
*   Fri Sep 21 2018 Dweep Advani <dadvani@vmware.com> 1.58-1
-   Update to version 1.58.
*   Tue Feb 20 2018 Xiaolin Li <xiaolinl@vmware.com> 1.54-2
-   Build perl-DBD-SQLite with sqlite-autoconf-3.22.0.
*   Mon Apr 3 2017 Robert Qi <qij@vmware.com> 1.54-1
-   Upgraded to 1.54.
*   Wed Nov 16 2016 Alexey Makhalov <ppadmavilasom@vmware.com> 1.50-3
-   Use sqlite-devel as a BuildRequires.
*   Tue May 24 2016 Priyesh Padmavilasom <ppadmavilasom@vmware.com> 1.50-2
-   GA - Bump release of all rpms.
*   Tue Feb 23 2016 Harish Udaiya Kumar <hudaiyakumar@vmware.com> 1.50-1
-   Upgraded to version 1.50.
*   Thu Jan 21 2016 Anish Swaminathan <anishs@vmware.com> 1.48-1
-   Upgrade version.
*   Fri Apr 3 2015 Divya Thaluru <dthaluru@vmware.com> 1.46-1
-   Initial version.
