# Changelog

## v2.5.0 (2026-05-13)

### Features

- V3.0.0 ([`a54488c`](https://github.com/nanorepublica/django-prodserver/commit/a54488c80b5bf481ba16f30257f56c6dda87c766))
- Add celeryflower backend for celery monitoring ([`81132ef`](https://github.com/nanorepublica/django-prodserver/commit/81132ef2c0bec91d331f47d4dbbe497abb3b8f94))
- Rename `prodserver` command to `server` (deprecate `prodserver`) ([`858cff9`](https://github.com/nanorepublica/django-prodserver/commit/858cff9ec08ddbe6aa86553eabb2eace3eea8372))
- Add werkzeugrunserver / runserverplus dev backend ([`3764b38`](https://github.com/nanorepublica/django-prodserver/commit/3764b38b2ac7c75ef0efaf2923a83721ad35da10))
- Add daphnerunserver asgi development backend ([`15975d4`](https://github.com/nanorepublica/django-prodserver/commit/15975d41dbd6f75be94f1c324dfe0d1448aaabe1))
- Add djangorunserver development backend ([`96c9222`](https://github.com/nanorepublica/django-prodserver/commit/96c9222c320b918342d143353ed2b0d1cbc38892))

### Bug fixes

- Make werkzeug's debugger actually fire on exceptions ([`27a8cd9`](https://github.com/nanorepublica/django-prodserver/commit/27a8cd9f9914c909b195851d8451013507a5a228))
- Don't double-wrap server class with threadingmixin ([`b272ad2`](https://github.com/nanorepublica/django-prodserver/commit/b272ad2ceacf9d1da50c4f6af7448cec43f1a170))
- Allow passing arguments without values ([`175cc01`](https://github.com/nanorepublica/django-prodserver/commit/175cc016aa6c86147d514a36c49d9fc55935b614))

## v2.4.0 (2025-12-04)

### Features

- Release ([`f7803a4`](https://github.com/nanorepublica/django-prodserver/commit/f7803a475e0f44eb1427510471542ce95ffbee41))

### Documentation

- Make the docs more concise ([`45252c6`](https://github.com/nanorepublica/django-prodserver/commit/45252c6a78f7e272b05d9f45d1f592e558e9ce03))
- Implement comprehensive user documentation ([`7d07706`](https://github.com/nanorepublica/django-prodserver/commit/7d077066e37f29066ec08ea94b071b61c1c466c5))
- Create tasks breakdown for user documentation ([`e851d0f`](https://github.com/nanorepublica/django-prodserver/commit/e851d0f6388b2804dadb1912b3704746a58bb392))
- Create comprehensive user documentation spec ([`24da4d7`](https://github.com/nanorepublica/django-prodserver/commit/24da4d7a4b9a1c8fc796473bc1c9bf1e45efd11f))
- Add requirements for user documentation spec ([`1fb4333`](https://github.com/nanorepublica/django-prodserver/commit/1fb43330dcae6772ae6f1436ddd13d7c396bdcb3))
- Initialize spec for comprehensive user documentation ([`ec6dd1a`](https://github.com/nanorepublica/django-prodserver/commit/ec6dd1a0c19de9687bfce01d003e84f990d40233))
- Add product planning documentation ([`12706f1`](https://github.com/nanorepublica/django-prodserver/commit/12706f1d16bb4917c61d9188829be85aa88c68a9))

## v2.3.0 (2025-10-08)

### Features

- Add granian as a server backend ([`1cafd80`](https://github.com/nanorepublica/django-prodserver/commit/1cafd804b97f5a2d093e844260676e9f24946d87))
- Add granian as a server backend ([`825d7b6`](https://github.com/nanorepublica/django-prodserver/commit/825d7b6c42c2931a9f12bf867e9a0bf33049b5c4))

## v2.2.0 (2025-09-06)

### Features

- Add backend for celery beat process ([`a0b2a9d`](https://github.com/nanorepublica/django-prodserver/commit/a0b2a9ddd74be99a84c79df2534c90f61441c908))

### Documentation

- Remove duplicated h1 tag on home page ([`4442588`](https://github.com/nanorepublica/django-prodserver/commit/44425882fa71d0f9b8a027f5c6ec3b50ecada26a))
- Move table of content after main readme ([`55816cc`](https://github.com/nanorepublica/django-prodserver/commit/55816cc99b47403d716db1a2889d57ef5d1a4169))

## v2.1.1 (2025-08-31)

### Bug fixes

- Incorrect argument handling in gunicorn backend" ([`02304ff`](https://github.com/nanorepublica/django-prodserver/commit/02304ffa29a70f76ce7a7bb987640c48c5224338))

## v2.1.0 (2025-08-31)

### Features

- Add django-q2 backend ([`5f4c58e`](https://github.com/nanorepublica/django-prodserver/commit/5f4c58e1645f8cd322e75d48f8ddae3ca4ba5058))

## v2.0.0 (2025-08-29)

### Features

- 1.0.0 release breaking change ([`c0712dd`](https://github.com/nanorepublica/django-prodserver/commit/c0712dd8bbe02fb19ae94e079c6b3b85e94f5ed9))

### Build system

- Version update ([`121b3e0`](https://github.com/nanorepublica/django-prodserver/commit/121b3e0c68f68b63b1fcca17019f820dd93fdcf8))
- Version update ([`4e7fe66`](https://github.com/nanorepublica/django-prodserver/commit/4e7fe66a7b1eea807130bb5fa902983cdec20220))

## v1.0.2 (2025-08-27)

### Build system

- Version update ([`80e48ba`](https://github.com/nanorepublica/django-prodserver/commit/80e48ba0c74b5be3878d865c9e245b9040072b3d))

## v1.0.0 (2025-08-26)

### Build system

- Coverage ([`9ecb36a`](https://github.com/nanorepublica/django-prodserver/commit/9ecb36a22095933cdbe5daf6b4f3342f7a833692))

### Documentation

- Fix types and updates ([`9a22dc6`](https://github.com/nanorepublica/django-prodserver/commit/9a22dc683a6bfd56657e5b3c76273bd300e96c0b))
- More docs improvements ([`6e3a3f6`](https://github.com/nanorepublica/django-prodserver/commit/6e3a3f66802430cabee1aee710af853c8cc19932))

## v0.0.0 (2025-04-28)
