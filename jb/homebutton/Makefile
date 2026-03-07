CC ?= clang
CFLAGS ?= -O2 -Wall -Wextra
LDFLAGS ?= -framework IOKit -framework CoreFoundation
TARGET := fake_button

.PHONY: all clean

all: $(TARGET)

$(TARGET): fake_button.c
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

clean:
	rm -f $(TARGET)
