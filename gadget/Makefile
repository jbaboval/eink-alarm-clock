
build:
	gadget build
	# Gadget doesn't support docker options (at least it's not documented...)
	# Rebuild the tagged image with --squash so we get a small image
	# without writing an uncacheable, unreadable Dockerfile
	cd .. && docker build --squash --tag gadget_543d9c13-cea9-4575-a290-a6dcba514dc6-img C:\Users\John.hackintosh\sandbox\eink-alarm-clock\gadget/../
