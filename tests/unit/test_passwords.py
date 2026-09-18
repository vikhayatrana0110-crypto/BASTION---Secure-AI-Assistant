from bastion.auth.passwords import hash_password, verify_password


def test_hash_does_not_contain_the_password():
    stored = hash_password("correct horse battery staple")

    assert "correct horse battery staple" not in stored
    assert stored.startswith("$argon2id$")


def test_correct_password_verifies():
    stored = hash_password("correct horse battery staple")

    assert verify_password("correct horse battery staple", stored) is True


def test_wrong_password_is_rejected():
    stored = hash_password("correct horse battery staple")

    assert verify_password("Correct horse battery staple", stored) is False


def test_same_password_hashes_differently_every_time():
    first = hash_password("same password")
    second = hash_password("same password")

    assert first != second
    assert verify_password("same password", first) is True
    assert verify_password("same password", second) is True


def test_damaged_hash_is_rejected_without_raising():
    assert verify_password("anything", "not-a-real-hash") is False