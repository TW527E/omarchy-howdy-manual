#define _GNU_SOURCE
#include <assert.h>
#include <security/pam_appl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct scenario { const char *answer; int calls; int cancel; };
static int converse(int count, const struct pam_message **messages,
                    struct pam_response **responses, void *data) {
    struct scenario *s = data;
    assert(count == 1);
    assert(messages[0]->msg_style == PAM_PROMPT_ECHO_OFF);
    assert(strcmp(messages[0]->msg,
        "Password (or press Enter for face recognition): ") == 0);
    s->calls++;
    if (s->cancel) return PAM_CONV_ERR;
    *responses = calloc(1, sizeof(**responses));
    assert(*responses);
    (*responses)[0].resp = s->answer ? strdup(s->answer) : NULL;
    if (s->answer) assert((*responses)[0].resp);
    return PAM_SUCCESS;
}
int main(int argc, char **argv) {
    assert(argc == 2);
    /* The face and password stubs fail unless their exact branch is allowed. */
    const char *services[] = {"face-ok", "face-denied", "password-ok", "both-denied"};
    for (int i = 0; i < 4; i++) {
        for (int choice = 0; choice < 4; choice++) {
            struct scenario s = {.answer = choice == 3 ? NULL : choice ? "test-only-password" : "", .cancel = choice == 2};
            struct pam_conv conv = {converse, &s};
            pam_handle_t *pamh = NULL;
            assert(pam_start_confdir(services[i], "test-user", &conv, argv[1], &pamh) == PAM_SUCCESS);
            int result = pam_authenticate(pamh, 0);
            int expected = (choice == 0 && i == 0) || (choice == 1 && i == 2);
            assert((result == PAM_SUCCESS) == expected);
            assert(s.calls == 1);
            pam_end(pamh, result);
        }
    }
    puts("PASS: 16 PAM stack cases (face, password, cancellation, null response, denied authentication)");
}
