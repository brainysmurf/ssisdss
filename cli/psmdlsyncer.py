"""
Command line stuff
"""

from ssis_dss.trees import AutosendTree, MoodleTree

import click
#import ssis_dss   #(see comment on line 14 for why this is commented out)

from cli.cli import CLIObject

@click.group()
@click.option('--test/--dont_test', default=False, help="Uses test information")
@click.option('--template', type=click.STRING, default=None, help="Define the template")
@click.option('--readfromdisk', type=click.File(mode='rb'), default=None, help="Readin pickled data")
@click.option('--writetodisk', type=click.File(mode='wb'), default=None, help="Write pickled data")
@click.pass_context
def psmdlsyncer(ctx, test, template, readfromdisk, writetodisk):
    # Doesn't do much now, but leave it as boilerplate for when there are global flags n such
    ctx.obj = CLIObject(test)
    ctx.obj.template = template

    if ctx.obj.test or template is None:
        template = "dss.templates.DefaultTemplate"
    else:
        template = "ssis_dss.templates.templates.{}".format(template)

    ctx.obj.init_psmdlsyncer(template, readfromdisk, writetodisk)

@psmdlsyncer.command("go")
@click.pass_obj
def psmdlsyncer_go(obj):
    if obj.test:
        click.echo("Doens't make sense to test with a go command, do you mean 'embed' instead?")
        return

    # Initiate the first-run, which only makes sense in this context
    from ssis_dss.trees import AutosendFirstrunTree, MoodleFirstrunTree
    autosendfr = AutosendFirstrunTree()
    moodlefr = MoodleFirstrunTree()
    moodlefr.set_template('ssis_dss.templates.templates.MoodleFirstRunTemplate')
    # populates just the user info
    print('Running first run:')
    +autosendfr
    +moodlefr
    # ensures the users are in the right cohorts
    pause = True

    autosendfr >> moodlefr

    print('Running second run')
    autosend = AutosendTree()
    moodle = MoodleTree()
    +autosend
    +moodle

    autosend >> moodle


@psmdlsyncer.command("output")
@click.option('--path', type=click.File(mode='w'), default=None, help="Output differences to text file")
@click.pass_obj
def psmdlsyncer_output(obj, path):
    +obj.source
    +obj.dest
    if path is None:
        for item in obj.source - obj.dest:
            print(item.message)
    else:
        for item in obj.source - obj.dest:
            path.write(item.message)
            path.write('\n')
    from IPython import embed;embed()

@psmdlsyncer.command("inspect")
@click.pass_obj
def psmdlsyncer_inspect(obj):
    """

    """
    # for item in obj.source - obj.dest:
    #     print(item.message)
    print("Reading in autosend...")
    +obj.source
    print("Reading in moodle...")
    +obj.dest
    autosend = obj.source
    moodle = obj.dest

    go_one = lambda idnumber: [a for a in autosend.go_filter(moodle, filter_={'idnumber':idnumber})]

    click.echo("You have 'autosend' and 'moodle' variables available")
    from IPython import embed;embed()

@psmdlsyncer.command("test_model")
@click.pass_obj
def psmdlsyncer_test_model(obj):
    +obj.source
    +obj.dest
    obj.source.test_model(obj.dest)

