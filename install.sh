#!/bin/bash
APPID="com.zeroneai.app"
BUNDLENAME="zeroneai.flatpak"

if [ "$1" = "meson" ]; then
	echo "Building with meson"
	meson setup builddir --prefix=/usr/bin
	ninja -C builddir
	sudo ninja -C builddir install
	exit
fi

flatpak-builder --install --user --force-clean flatpak-app "$APPID".json

if [ "$1" = "bundle" ]; then
	flatpak build-bundle ~/.local/share/flatpak/repo "$BUNDLENAME" "$APPID"
fi
