Concourse pipeline maker - Generate Conconse pipeline from smaller chunks
===

## Objectif

The primary goal of this tool is to generate the pipeline manifest required by the ressource [concourse-pipeline-resource](https://github.com/concourse/concourse-pipeline-resource).

Additionally, it provide feature to improve the maintainability of your pipelines, such as:
  * Generating command line to manually set pipeline
  * Merge of pipeline (Therefore you can split yout yaml configuration in multiple files or override existing configuration)
  * Templating (reuse a configuration to generate similar pipeline)

## Usage

```
CONCOURSE PIPELINE MAKER

Usage:
  cpm [--ifile <inputfile>] [--ofile <outputfile>]
    [-p <text_to_search:replacement_text>...] [options]
  cpm <pipeline_name>... [--ifile <inputfile>] [--ofile <outputfile>]
    [-p <text_to_search:replacement_text>...] [options]
  cpm -h | --help

Options:
  -i <inputfile>, --ifile <inputfile>       Path to the pipeline manifest. [default: pipelinemanifest.json]
  -o <outputfile>, --ofile <outputfile>     Path to the output folder. [default: ./pipelines_files]
  -p <text_to_search:replacement_text>      Search and replace operation applied before procssing the pipeline manifest.
                                            Very usefull when working locally.
  -c <sfolder>, --ci <sfolder>              When publishing pipelines in a repo make sure it is compatible with concourse/concourse-pipeline-resource
  -x <cli_ext>, --cli <cli_ext>             Generate the Fly command line for each pipeline [default: cmd]
  Options-Flags:
  --copy                                    Systematically copy the pipeline in the output directory.
  --debug                                   Set the log level to debug
  -h, --help                                Show the help screen.
```

## Define pipeline

`cpm` uses a manifest called `pipelinemanifest.json` (by default, yaml format is also supported). This manifest contain the `fly set-pipeline` parameters for each pipeline to be set.

For instance:

```sh
fly set-pipeline -t achat \
  -p service-dummy \
  -c ./pipelines/services-pipeline.yml \
  --load-vars-from ./vars/vars-dev.yml \
  --var "artifact_id=service-dummy"\
  --var "repo_id=service-dummy"
```

Is translated into a JSON object as follow:

```json
{
  "configs": {},
  "templates": {},
  "pipelines":[
    {"-p": "service-dummy",
      "-c": "pipelines/services-pipeline.yml",
      "load-vars-from": "vars/vars-dev.yml",
      "var": {"artifact_id": "service-dummy", "repo_id": "service-dummy"}
    }
  ]
}
```

* The `configs` section may be use to define configuration that will be applied to every the pipeline
* The `template`section may be use to create reusable configuration. Later you can apply it by using the key `-tpl` ot `template` in your pipeline configuration
* The `pipelines` section define the individual configuration for each pipeline

### Valide pipeline configuration

* Arguments of `fly set_pipeline`: 
  * `-t`, `team`: team / target
  * `pipeline`, `-p`: pipeline name (string)
  * `config`, `-c`: configurqation file for the pipeline (string)
  * `load-vars-from`, `-l`: variables file(s) (string or array)
  * `var`, `-v`: variables (JSON object)

* Argument de templating
    * `-tpl`, `template`: template to be use as a base for this pipeline

* Argument de fusion de pipeline
    * `-m`, `merge`: yaml file(s) to be merge together in order (string or array)
    * `patials`: if provide folder name in `config`, `-c`, then you can list all the files you want to merge together from that folder

## Example of configuration with merge and template

```json
{
  "configs": {
    "-t": "team",
    "-l": "./pipelines_assets/vars-configs.yml",
    "-v": {
      "config": 1
    }
  },
  "templates": {
    "template": {
      "-c": "./pipelines_assets/pipeline.yml",
      "-l": "./pipelines_assets/vars-template.yml",
      "-v": {
        "test": 1,
        "tests": 2
      }
    }
  },
  "pipelines": [
    {
      "-p": "Test",
      "-tpl": "template",
      "-v": {
        "test": 7
      }
    }
  ]
}
```

## Example of configuration with Partials

This configuration will create a ppeline called `Test` by merging the files:
  * path/to/pipeline/folder/buid_it.yml
  * path/to/pipeline/folder/test_it.yml
  * path/to/pipeline/folder/ship_it.yml

```json
{
  "configs": {
    "-t": "team"
  },
  "templates": {},
  "pipelines": [
    {
      "-p": "Test",
      "-c": "path/to/pipeline/folder/",
      "partials": [
        "buid_it",
        "test_it",
        "ship_it"
      ]
    }
  ]
}
```

## Example of configuration with Partials and inplace replace

This configuration will create a ppeline called `Test` by merging the files:
  * path/to/pipeline/folder/buid_it.yml
  * path/to/pipeline/folder/test_it.yml
  * path/to/pipeline/folder/ship_it.yml and replace **((var))** by `foo`
  * path/to/pipeline/folder/ship_it.yml and replace **((var))** by `bar`

```json
{
  "configs": {
    "-t": "team"
  },
  "templates": {},
  "pipelines": [
    {
      "-p": "Test",
      "-c": "path/to/pipeline/folder/",
      "partials": [
        "buid_it",
        "test_it",
        {"config_file": "ship_it", "with": { "var": "foo"}},
        {"config_file": "ship_it", "with": { "var": "bar"}}
      ]
    }
  ]
}
```

## Use case of cpm

I wanna generate and set pipelines locally:
```bash
# Process the pipeline manifest
cpm
# Process only 1 pipeline and give me the fly command to execute
cpm my_pipilene
# Process all pipeline and generate the fly command line as .cmd files
cpm --cli cmd
# Process all pipeline and generate the fly command line as .sh files
cpm --cli sh
# Process all pipeline and copy all files in the output folder
cpm --copy
# My pipeline are in an other location and I use a generic name for it
cpm -p alias:path/to/the/folder
```


## Reusable commandline configuration (.cpmrc)

You may choose to define a runtime configuration in a file `.cpmrc`. Place that file at the location you arr usually run cpm from and paste into it your configuration.

Cpm configuration is printed at each execution in the terminal and look like this:

```json
{
  "--ci": None,
  "--cli": False,
  "--copy": False,
  "--debug": False,
  "--help": False,
  "--ifile": "pipelinemanifest.json",
  "--ofile": "./pipelines_files",
  "-p": [],
  "<pipeline_name>": []
}
```