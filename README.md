# Directory Configuration
```
├── README.md
├── lambda_function
│   └── handler.py
└── tests
    ├── secret_config.py
    ├── test_extract_data.py
    ├── test_is_reaction_message.py
    ├── test_post_message.py
    ├── test_post_message_mock.py
    └── test_verify_request.py
```

# How to Set Up

## Lambda Layer

To use the Slack SDK in a Lambda function, we will create a Lambda Layer. Follow the steps below to create a zip file, and then use that file to create a new Layer.

```
mkdir python
cd python
pip install slack_sdk -t .
cd ..
zip -r layer-slack.zip python
```

# How to Test
You can execute the test code using `pytest`. By running the `pytest` command without arguments, it will execute all test codes under the `tests/` directory.

```
cd $PROJECT_ROOT
pytest
```

If you want to run a specific test code, specify the target file as an argument like the following:

```
pytest tests/test_verify_request.py
```

Some of the tests use secret data (such as Slack Token) defined in `tests/secret_config.py`. Therefore, you need to prepare various secret information in advance, referring to `secret_config.py.dummy`.




