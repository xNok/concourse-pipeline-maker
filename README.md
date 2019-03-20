Utiliser le Concourse pipeline Maker et mettre à jour le pipeline manifest
===

## Objectif

The primary goal of this tool is to generate the pipeline manifest required by the ressource [concourse-pipeline-resource](https://github.com/concourse/concourse-pipeline-resource).

Additionally, it provide feature to improve the maintainability of your pipelines, such as:
  * Generating command line to manually set pipeline
  * Merge of pipeline (split configuration in multiple files or override existing configuration)
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
Options-Flags:
  --cli                                     Generate the Fly command line for each pipeline
  --copy                                    Systematically copy the pipeline in the output directory.
  --debug                                   Set the log level to debug
  --fly3                                    Retro-compatibility with concourse and fly 3
  -h, --help                                Show the help screen.
```

## Define pipeline

`cpm` uses a manifest `pipelinemanifest.json` (by default). This manifest contain the `fly set-pipeline` parameters.

For instance:

```sh
fly set-pipeline -t achat \
  -p service-dummy \
  -c ./consourse/pipelines/nonprod-services-pipeline.yml \
  --load-vars-from ./consourse/vars/vars-nonproduction.yml \
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

* The `configs` section may be use to define configuration that will be applied to all the pipeline
* The `template`section may be use to create reusable configuration. Later you can apply the using the key `-tpl`, `template` in your pipeline configuration
* The `pipelines` section define the individual configuration for each pipeline

## Valide pipeline configuration

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

## Use case of cpm

I wanna generate and set pipelines locally:
```bash
# Process the pipeline manifest
cpm
# Process only 1 pipeline and give me the fly command to execute
cpm my_pipilene
# Process all pipeline and generate the fly command line as .cmd files
cpm --cli
# Process all pipeline and copy all files in the output folder
cpm --copy
# My pipeline are in an other location and I use a generic name for it
cpm -p alias:path/to/the/folder
```

## Example of merge and template configuration


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