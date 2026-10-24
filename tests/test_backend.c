#include <security/pam_modules.h>
#include <string.h>
PAM_EXTERN int pam_sm_authenticate(pam_handle_t *pamh, int flags, int argc, const char **argv) {
    (void)flags;
    const void *token = 0;
    if (argc != 1 || pam_get_item(pamh, PAM_AUTHTOK, &token) != PAM_SUCCESS || !token)
        return PAM_AUTH_ERR;
    const char *expected = strcmp(argv[0], "face") == 0 ? "" : "test-only-password";
    return strcmp(token, expected) == 0 ? PAM_SUCCESS : PAM_AUTH_ERR;
}
