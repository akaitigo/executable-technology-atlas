#include <banner.h>
extern int puts(const char *);
int main(void) { return puts(BANNER) < 0; }
